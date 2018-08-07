from pyramid.config import Configurator


class ModelPredicate:
    def __init__(self, val, config):
        self.val = val

    def text(self):
        return "model = {}".format(self.val)

    phash = text

    def __call__(self, context, request):
        if isinstance(self.val, tuple):
            return request.matchdict.get("model_name") in self.val
        return request.matchdict.get("model_name") == self.val


class AttributePredicate:
    def __init__(self, val, config):
        self.val = val.lower()

    def text(self):
        return "attribute = {}".format(self.val)

    phash = text

    def __call__(self, context, request):
        if isinstance(self.val, tuple):
            return request.matchdict.get("attribute") in self.val
        return request.matchdict.get("attribute").lower() == self.val


def includeme(config: Configurator):
    config.add_view_predicate("model", ModelPredicate)
    config.add_view_predicate("attribute", AttributePredicate)
