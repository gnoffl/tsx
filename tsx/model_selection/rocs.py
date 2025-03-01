from hashlib import md5

class ROC_Member:

    ''' Object representing a member of a Region of Competence

    Args:
        x (`np.ndarray`): Original time series values
        y (`np.ndarray`): Corresponding true forecasting values
        indices (`np.ndarray`): Indices indicating the salient region

    Attributes:
        r (`np.ndarray`): Most salient subseries of `x`
        x (`np.ndarray`): Original time series values
        y (`np.ndarray`): Corresponding true forecasting values
        indices (`np.ndarray`): Indices indicating the salient region

    '''
    def __init__(self, x, y, indices):
        self.x = x
        self.y = y
        self.r = x[indices]
        self.indices = indices

    def __repr__(self):
        return ', '.join(str(v.round(4)) for v in self.r)

    def __hash__(self):
        representation = self.__repr__()
        return int(md5(representation.encode('utf-8')).hexdigest(), 16) & 0xffffffff

