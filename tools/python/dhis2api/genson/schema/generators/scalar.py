from .base import SchemaGenerator, TypedSchemaGenerator
import re
from titlecase import titlecase


class Typeless(SchemaGenerator):
    """
    schema generator for schemas with no type. This is only used when
    there is no other active generator, and it will be merged into the
    first typed generator that gets added.
    """

    @classmethod
    def match_schema(cls, schema):
        return 'type' not in schema

    @classmethod
    def match_object(cls, obj):
        return False


class Null(TypedSchemaGenerator):
    """
    generator for null schemas
    """
    JS_TYPE = 'null'
    PYTHON_TYPE = type(None)


class Boolean(TypedSchemaGenerator):
    """
    generator for boolean schemas
    """
    JS_TYPE = 'boolean'
    PYTHON_TYPE = bool


class String(TypedSchemaGenerator):
    """
    generator for string schemas - works for ascii and unicode strings
    """
    JS_TYPE = 'string'
    PYTHON_TYPE = (str, type(u''))

    def get_format(self,obj,parent):
        """
        work out the most likely format
        """

        if re.match(r"^htt", obj):
            # Anything beginning with "htt..." is assumed to be a url
            format = "url"

        elif re.match(r"^ou$|^pe$|^dx|^dy$", obj):
            # Anything beginning with "htt..." is assumed to be a url
            format = "dimension"

        elif re.match(r"[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$", obj):
            # a typical email format
            format = "email"

        elif re.match(r"\[+-*[0-9.]+,-*[0-9.]+\].*$", obj):
            # a typical email format
            format = "coordinates"

        elif re.match(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z*", obj):
            # the ISO date-time used by DHIS2
            format = "date-time"

        elif re.match(r"^[0-9a-zA-Z]{11}$", obj):
            # a mix of 11 alphanumeric chars "might" be a DHIS2 UID - lets do some more checks...
            format = "uid"
            if "id" != parent.lower():
                # OK, this might not be a uid
                if parent[-4:].lower() in ["name","code"]:
                        # names are general format
                        format = "general"
                elif "value" == parent.lower():
                    # codes are usually general format
                    format = "general"
                elif re.match(r"^[A-Z_]+$", obj):
                    # All upper-case or underscore, could be an ENUM
                    #print("enumsub")
                    format = "enum"
                elif re.match(r"^[a-zA-Z ]+$", obj):
                    if obj == titlecase(obj.lower()):
                        # A string in titlecase is assumed to be a generic name
                        #print("gensub:",obj,titlecase(obj.lower()))
                        format = "general"

        elif re.match(r"^#[0-9a-fA-F]{6}$", obj):
            format = "COLOR"

        elif re.match(r"^[A-Z_]+$", obj):
            format = "enum"
            if parent[-4:].lower() in ["name","code"]:
                    # names are general format
                    format = "general"
            elif "value" == parent.lower():
                # codes are usually general format
                format = "general"

        elif re.match(r"^[A-Z]_[a-zA-Z_-]+$", obj):
            format = "enum"
            if parent[-4:].lower() in ["name","code"]:
                    # names are general format
                    format = "general"
            elif "value" == parent.lower():
                # codes are usually general format
                format = "general"

        elif re.match(r"^[-rw]+$", obj):
            format = "access"

        else:
            format = "general"

        #print("\tobj:",parent, obj,"format:",format)
        return format

    def add_object(self, obj, parent, mode):
        # print("add_obj",parent)
        if self.MIN is None or len(obj) < self.MIN:
            if mode != "learn":
                # testing mode
                self.SCHEMA_ERROR += ['value smaller than schema minimum']
            self.MIN = len(obj)
        if self.MAX is None or len(obj) > self.MAX:
            if mode != "learn":
                # testing mode
                self.SCHEMA_ERROR += ['value larger than schema maximum']
            self.MAX = len(obj)
        newFormat = self.get_format(obj,parent)
        if self.FORMAT == "enum":
            self.ENUM.add(obj)
        else:
            self.ENUM.clear()
            self.ENUM = set()
        #cannot change from dimension or general to uid
        if self.FORMAT in ["dimension","general"]:
            if newFormat == "uid":
                newFormat = self.FORMAT

        if self.FORMAT is None or newFormat != self.FORMAT:
            if self.FORMAT is not None:
                print("FORMAT_CHANGE:",parent,self.FORMAT,newFormat,obj)

            if mode != "learn" and newFormat != None:
                # testing mode
                self.SCHEMA_ERROR += ['value format '+newFormat+' does not match schema format '+ self.FORMAT]
            self.FORMAT = newFormat
        if self.EXAMPLE is None:
            if self.FORMAT == "general":
                self.EXAMPLE = "my"+parent
                if len(self.EXAMPLE) > self.MAX:
                    self.EXAMPLE = self.EXAMPLE[:self.MAX-1]
            else:
                # print(parent,obj)
                self.EXAMPLE = obj



class Number(SchemaGenerator):
    """
    generator for integer and number schemas. It automatically
    converts from `integer` to `number` when a float object or a
    number schema is added
    """
    JS_TYPES = ('integer', 'number')
    PYTHON_TYPES = (int, float)

    @classmethod
    def match_schema(cls, schema):
        return schema.get('type') in cls.JS_TYPES

    @classmethod
    def match_object(cls, obj):
        return type(obj) in cls.PYTHON_TYPES

    def init(self):
        self._type = 'integer'
        self.FORMAT = 'int32'
        #print("INIT number") #PPPP

    def add_schema(self, schema):
        #print("AddSchemaObject--",obj) #PPPP
        self.add_extra_keywords(schema)
        if schema.get('type') == 'number':
            self._type = 'number'

    def add_object(self, obj, parent, mode):
        #print("AddNumberObject--",obj) #PPPP
        if self.MIN is None or obj < self.MIN:
            if mode != "learn":
                # testing mode
                print(obj ,"smaller than schema min", self.MIN)
            self.MIN = obj
        if self.MAX is None or obj > self.MAX:
            if mode != "learn":
                # testing mode
                print(obj, "larger than schema max", self.MAX)
            self.MAX = obj
        if isinstance(obj, float):
            self._type = 'number'
            self.FORMAT = 'double'
        if self.EXAMPLE is None:
            self.EXAMPLE = obj

    def to_schema(self):
        schema = super(Number, self).to_schema()
        schema['type'] = self._type
        schema['minimum'] = self.MIN
        schema['maximum'] = self.MAX
        schema['format'] = self.FORMAT
        schema['example'] = self.EXAMPLE
        if len(self.ENUM):
            schema['enum'] = list(self.ENUM)
        if len(self.SCHEMA_ERROR):
            schema['schema_error'] = self.SCHEMA_ERROR
        #print("NumberToSchema---",self.MIN) #PPPP
        return schema
