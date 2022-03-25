from elasticsearch_dsl import Q


class AggBase:
    insert_into_parent = False

    def __init__(
        self, code, nested=None, parent=None, label=None, display=True, **kwargs
    ):
        self.code = code
        self.label = label
        self.parent = parent
        self.display = display
        self.nested = list(nested or ())
        self.kwargs = kwargs

    def apply(self, agg):
        if self.display:
            for n in self.nested:
                n.apply(agg)
        return agg

    def _append(self, item_type, *args, **kwargs):
        if self.insert_into_parent and self.parent:
            return self.parent._append(item_type, *args, **kwargs)
        b = item_type(*args, **kwargs)
        self.nested.append(b)
        b.parent = self
        return b

    def bucket(self, *args, **kwargs):
        return self._append(BucketAgg, *args, **kwargs)

    def separator(self):
        self._append(SeparatorAgg)
        return self

    @property
    def top(self):
        if self.parent:
            return self.parent.top
        return self

    def process_result(self, data):
        if self.code not in data:
            return None

        my_data = data.pop(self.code)

        ret = {"code": self.code}
        missing_key = self.code + ".__missing__"
        if missing_key in data and "doc_count" in data[missing_key]:
            ret["__missing__"] = data.pop(missing_key)["doc_count"]

        count_key = self.code + ".__count__"
        if count_key in data and "value" in data[count_key]:
            ret["__count__"] = data.pop(count_key)["value"]

        if self.label:
            ret["label"] = self.label

        if self.nested:
            sub_facets = []
            for n in self.nested:
                r = n.process_result(my_data)
                if r:
                    sub_facets.append(r)
            ret["facets"] = sub_facets
        ret.update(my_data)
        return ret

    def filter(self, facets_and_values):
        if self.nested:
            for n in self.nested:
                yield from n.filter(facets_and_values)


class BucketAgg(AggBase):
    insert_into_parent = True

    def __init__(self, code, type="terms", field=None, **kwargs):
        super().__init__(code, **kwargs)
        self.type = type
        self.field = field or code

    def apply(self, agg):
        if self.display:
            agg.bucket(
                self.code + ".__missing__", "missing", field=self.field, **self.kwargs
            )
            agg.bucket(
                self.code + ".__count__", "value_count", field=self.field, **self.kwargs
            )
            ret = agg.bucket(self.code, self.type, field=self.field, **self.kwargs)
            return super().apply(ret)
        else:
            return agg

    def filter(self, facets_and_values):
        values = self.get_values(facets_and_values)
        if values:
            not_missing = [
                x for x in values if x != "--missing--" and x != "--exists--"
            ]
            missing = [x for x in values if x == "--missing--"]
            exists = [x for x in values if x == "--exists--"]
            if not_missing:
                yield Q("terms", **{self.field: values})
            if missing:
                yield Q("bool", must_not=Q("exists", field=self.field))
            if exists:
                yield Q("exists", field=self.field)
        yield from super().filter(facets_and_values)

    def get_values(self, facets_and_values):
        return facets_and_values.get(self.code, None)


class TranslatedBucketAgg(BucketAgg):
    def __init__(self, code, type="terms", field=None, map=None, **kwargs):
        super().__init__(code, type=type, field=field, **kwargs)
        self.map = map or {}
        self.inverse_map = {v: k for k, v in self.map.items()}

    def get_values(self, facets_and_values):
        ret = super().get_values(facets_and_values)
        if ret:
            ret = [self.inverse_map.get(x, x) for x in ret]
        return ret

    def process_result(self, data):
        ret = super().process_result(data)
        if "buckets" in ret:
            ret["buckets"] = [
                {
                    **x,
                    "key": self.map.get(x["key"], None)
                    or self.map.get("key_as_string", None)
                    or x["key"],
                }
                for x in ret["buckets"]
            ]
        return ret


class NestedAgg(AggBase):
    def __init__(self, code, path=None, **kwargs):
        super().__init__(code, **kwargs)
        self.path = path or code

    def apply(self, agg):
        if self.display:
            ret = agg.bucket(self.code, "nested", path=self.path)
            return super().apply(ret)
        else:
            return agg

    def filter(self, facets_and_values):
        children = list(super().filter(facets_and_values))
        if children:
            yield Q("nested", path=self.path, query=Q("bool", must=children))
