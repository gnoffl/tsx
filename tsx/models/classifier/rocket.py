import torch
import pickle
import torch.nn as nn
import numpy as np

from os.path import join

from sklearn.linear_model import RidgeClassifierCV
from tsx.models.classifier import BaseClassifier

class ROCKET(BaseClassifier):

    # TODO: Only for equal-length datasets?
    # TODO: Pytorch version appears to be very unstable. Needs more work
    def __init__(self, input_length=10, k=10_000, ridge=True, ppv_only=False, use_sigmoid=False, **kwargs):
        super(ROCKET, self).__init__(**kwargs)
        self.k = k
        self.ridge = ridge
        self.input_length = input_length
        self.ppv_only = ppv_only
        self.use_sigmoid = False

        self.kernels = []
        self.inform("Start building kernels")
        self.build_kernels()
        self.inform("Finished building kernels")

        if self.ridge:
            self.classifier = RidgeClassifierCV(alphas = np.logspace(-3, 3, 10), normalize = True)
        else:
            if ppv_only:
                self.classifier = nn.Sequential(nn.Linear(self.k, self.n_classes), nn.Softmax(dim=-1))
            else:
                self.classifier = nn.Sequential(nn.Linear(2*self.k, self.n_classes), nn.Softmax(dim=-1))

    def save(self):
        torch.save(self.kernels, 'rocket.kernels')
        if self.ridge:
            pickle.dump(self.classifier, open('rocket.classifier', 'wb'))
        else:
            torch.save(self.classifier.state_dict(), 'rocket.classifier')

    def load(self, path):
        self.kernels = torch.load(join(path, 'rocket.kernels'))
        if self.ridge:
            with open(join(path, 'rocket.classifier'), 'rb') as fp:
                self.classifier = pickle.load(fp)
        else:
            self.classifier.load_state_dict(torch.load(join(path, 'rocket.classifier')))

    def build_kernels(self):
        for i in range(self.k):
            kernel_length = [7, 9, 11][np.random.randint(0, 3)]

            weights = torch.normal(torch.zeros(1,1,kernel_length), 1)
            weights = weights - torch.mean(weights)

            bias = torch.rand(1)
            bias = (-1 - 1) * bias + 1

            # Parameter for dilation
            A = np.log2((self.input_length-1) / (float(kernel_length)-1))
            dilation = torch.floor(2**(torch.rand(1)*A)).long().item()

            padding = 0 if torch.rand(1)>0.5 else 1

            kernel = nn.Conv1d(1, 1, kernel_size=kernel_length, stride=1, padding=padding, dilation=dilation, bias=True)
            kernel.weight = nn.Parameter(weights, requires_grad=False)
            kernel.bias = nn.Parameter(bias, requires_grad=False)
            kernel.require_grad = False

            self.kernels.append(kernel)

    def transform(self, X):
        if isinstance(X, type(np.zeros(1))):
            X = torch.from_numpy(X)

        return self.apply_kernels(X)

    def fit(self, X_train, y_train, X_test=None, y_test=None):
        self.inform("Start fitting")
        if self.ridge:
            # Custom `fit` for Ridge regression
            X_train, y_train, X_test, y_test = self.preprocessing(X_train, y_train, X_test=X_test, y_test=y_test)
            self.classifier.fit(X_train, y_train)
            if X_test is not None and y_test is not None:
                print("ROCKET: Test set accuracy", self.classifier.score(X_test, y_test))
            self.fitted = True
        else:
            super().fit(X_train, y_train, X_test=X_test, y_test=y_test)

        self.inform("Finished fitting")

    def apply_kernels(self, X):
        features_ppv = []
        features_max = []
        with torch.no_grad():
            for i in range(self.k):
                if len(X.shape) == 2:
                    X = X.unsqueeze(1) # missing channel information

                transformed_data = self.kernels[i](X)

                features_ppv.append(self._ppv(transformed_data, dim=-1))
                if not self.ppv_only:
                    features_max.append(torch.max(transformed_data, dim=-1)[0])

            features_ppv = torch.cat(features_ppv, -1)
            if self.ppv_only:
                return features_ppv
            else:
                features_max = torch.cat(features_max, -1)
                return torch.cat((features_ppv, features_max), -1)

    def _ppv(self, x, dim=-1):
        # use sigmoid as a soft approximation for ">" activation
        if self.use_sigmoid:
            return torch.mean(torch.sigmoid(x), dim=-1)
        return torch.mean((x > 0).float(), dim=-1)

    def preprocessing(self, X_train, y_train, X_test=None, y_test=None):
        self.inform("Start preprocessing")
        X_train = self.apply_kernels(X_train)

        if X_test is not None:
            X_test = self.apply_kernels(X_test)

        self.inform("Finished preprocessing")
        return X_train, y_train, X_test, y_test

    def forward(self, x):
        if self.ridge:
            return self.classifier.predict(x)
        else:
            return self.classifier(x)
    