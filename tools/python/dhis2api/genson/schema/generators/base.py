from copy import copy
from warnings import warn


class SchemaGenerator(object):
    """
    base schema generator. This contains the common interface for
    all subclasses:

    * match_schema
    * match_object
    * init
    * add_schema
    * add_object
    * to_schema
    """
    KEYWORDS = ('type','min','minimum','minLength','minItems','max','maximum','maxLength','maxItems','format','enum','example','unique', 'default')

    @classmethod
    def match_schema(cls, schema):
        raise NotImplementedError("'match_schema' not implemented")

    @classmethod
    def match_object(cls, obj):
        raise NotImplementedError("'match_object' not implemented")

    def __init__(self, node_class):
        self.node_class = node_class
        self.MIN = None
        self.MAX = None
        self.FORMAT = None
        self.EXAMPLE = None
        self.UNIQUE = None
        self.ENUM = set()
        self.SCHEMA_ERROR = []
        self._extra_keywords = {}
        # self.kwm = {
        #     "max":self.MAX,
        #     "min":self.MIN,
        #     "format":self.FORMAT,
        #     "example":self.EXAMPLE,
        #     "unique":self.UNIQUE
        # }
        self.init()

    def init(self):
        pass

    def add_schema(self, schema):
        self.add_extra_keywords(schema)

    def add_extra_keywords(self, schema):
        for keyword, value in schema.items():
            if keyword in self.KEYWORDS:
                if keyword in ["max","maximum","maxLength","maxItems"]:
                    self.MAX = value
                if keyword in ["min","minimum","minLength","minItems"]:
                    self.MIN = value
                if keyword == "format":
                    self.FORMAT = value
                if keyword == "example":
                    self.EXAMPLE = value
                if keyword == "unique":
                    self.UNIQUE = value
                if keyword == "enum":
                    for v in value:
                        self.ENUM.add(v)

                continue
            elif keyword not in self._extra_keywords:
                self._extra_keywords[keyword] = value
            elif self._extra_keywords[keyword] != value:
                # warn(('Schema incompatible. Keyword {0!r} has conflicting '
                #       'values ({1!r} vs. {2!r}). Using {2!r}').format(
                #           keyword, self._extra_keywords[keyword], value))
                self._extra_keywords[keyword] = value

    def add_object(self, obj, parent, mode="learn"):
        pass

    def to_schema(self):
        return copy(self._extra_keywords)


class TypedSchemaGenerator(SchemaGenerator):
    """
    base schema generator class for scalar types. Subclasses define
    these two class constants:

    * `JS_TYPE`: a valid value of the `type` keyword
    * `PYTHON_TYPE`: Python type objects - can be a tuple of types
    """

    @classmethod
    def match_schema(cls, schema):
        return schema.get('type') == cls.JS_TYPE

    @classmethod
    def match_object(cls, obj):
        return isinstance(obj, cls.PYTHON_TYPE)

    def to_schema(self):
        schema = super(TypedSchemaGenerator, self).to_schema()
        schema['type'] = self.JS_TYPE
        if schema['type'] != "boolean":
            schema['format'] = self.FORMAT
            if schema['type'] == "string":
                if schema['format'] != "enum":
                    schema['minLength'] = self.MIN
                    schema['maxLength'] = self.MAX
            else:
                schema['min'] = self.MIN    
                schema['max'] = self.MAX
            schema['example'] = self.EXAMPLE
            if self.UNIQUE:
                schema['unique'] = self.UNIQUE
            if len(self.ENUM):
                schema['enum'] = list(self.ENUM)
        
        if len(self.SCHEMA_ERROR):
            schema['schema_error'] = self.SCHEMA_ERROR

        # remove attributes with null values from schema
        remove = []
        for n in schema:
            if not schema[n]:
                remove.append(n)
        for r in remove:
            del schema[r]
        return schema
