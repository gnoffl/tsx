import torch
import torch.nn as nn

def get_linear(L, n_classes):
    return nn.Sequential(
        nn.Linear(L, n_classes),
        nn.Softmax(dim=-1),
    )

def get_fcn(L, n_classes, n_hidden=32, depth=3):
    assert depth >= 2
    model = nn.ModuleList()
    for i in range(depth):
        if i == 0:
            model.append(nn.Linear(L, n_hidden))
            model.append(nn.ReLU())
        elif i == depth-1:
            model.append(nn.Linear(n_hidden, n_classes))
            model.append(nn.Softmax(dim=-1))
        else:
            model.append(nn.Linear(n_hidden, n_hidden))
            model.append(nn.ReLU())

    return nn.Sequential(*model)

def get_1d_cnn(L, n_classes, n_channels=1, depth_feature=2, depth_classification=2, n_hidden_neurons=32, n_hidden_channels=16):
    model = nn.ModuleList()

    for i in range(depth_feature):
        if i == 0:
            model.append(nn.Conv1d(n_channels, n_hidden_channels, kernel_size=3, padding='same'))
            model.append(nn.ReLU())
        else:
            model.append(nn.Conv1d(n_hidden_channels, n_hidden_channels, kernel_size=3, padding='same'))
            model.append(nn.ReLU())

    model.append(nn.Flatten())

    for i in range(depth_classification):
        if i == 0:
            model.append(nn.Linear(L * n_hidden_channels, n_hidden_neurons))
            model.append(nn.ReLU())
        elif i == depth_classification-1:
            model.append(nn.Linear(n_hidden_neurons, n_classes))
            model.append(nn.Softmax(dim=-1))
        else:
            model.append(nn.Linear(n_hidden_neurons, n_hidden_neurons))
            model.append(nn.ReLU())

    return nn.Sequential(*model)
