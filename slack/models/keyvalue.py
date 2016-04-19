"""
a Django model implementing a namespaced key-value storage

USAGE
    see the docstring of KeyValueStore
    
    
Copyright (c) Stefan LOESCH, oditorium 2016. All rights reserved.
Licensed under the Mozilla Public License, v. 2.0 <https://mozilla.org/MPL/2.0/>

based on https://djangosnippets.org/snippets/2451/ by Morgul
"""
__version__ = "2.0"
__version_dt__ = "2016-04-04"
__copyright__ = "Stefan LOESCH, oditorium 2016"
__license__ = "MPL v2.0"

from django.db import models
from itertools import chain
#from django.conf import settings


###########################################################################################
## KEY VALUE STORE BASE

class KeyValueStoreBase(object):
    """
    abstract base class defining the key-value store interface
    """

    ##################################################################
    ## DICT INTERFACE PROPERTIES AND METHODS

    def __getitem__(self, key):
        raise NotImplementedError()
 
    def get(self, key, default=None):
        """
        gets the value for a given key in this storage segment (or default)
        """
        try: return self[key]
        except KeyError: return default   
    
    def __setitem__(self, key, value):
        raise NotImplementedError()

    def __delitem__(self, key):
        raise NotImplementedError()

    def __contains__(self, key):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()

    def keys(self):
        raise NotImplementedError()

    def __iter__(self):
        return self.keys().__iter__()
        
    def values(self):
        raise NotImplementedError()

    def items(self):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

        
    ##################################################################
    ## OTHER PROPERTIES AND METHODS

    @property
    def as_dict(self):
        raise NotImplementedError()

    _parent = None
    @property
    def parent(self):
        """
        the object's parent object
        """
        if self._parent == None: return NullKeyValueStore()
        return self._parent

    @property
    def height(self):
        return 1 + self.parent.height

    @staticmethod
    def parent_namespace(namespace, hierarchy_separator):
        """returns the name of the parent namespace, or None"""
        try: return namespace.rsplit(hierarchy_separator, 1)[-2]
        except IndexError: return None 
        
    ##################################################################
    ## GLOBAL METHODS

    @classmethod
    def kvs_exists(cls, namespace):
        raise NotImplementedError()

    @classmethod
    def kvs_get(cls, namespace=None, create_if_not_exist=True):
        raise NotImplementedError()

    RAISE = 0
    CLEAR = 1
    UPDATE = 2 
    @classmethod
    def kvs_update(cls, namespace=None, dct=None, action_if_exists=None):
        raise NotImplementedError()

    @classmethod
    def kvs_delete(namespace):
        raise NotImplementedError()


###########################################################################################
## NULL KEY VALUE STORE
class NullKeyValueStore(KeyValueStoreBase):
    """
    the null key value store, not allowing to store any data
    
    this store is useful as root for hierarchical stores
    """
    
    @property
    def namespace(self):
        return ""

    ##################################################################
    ## DICT INTERFACE PROPERTIES AND METHODS

    def __getitem__(self, key):
        raise KeyError()
        
    def __setitem__(self, key, value):
        raise RuntimeError("can't set items in the null value store")

    def __delitem__(self, key):
        raise KeyError

    def __contains__(self, key):
        return False

    def __len__(self):
        return 0

    def keys(self):
        return {}.keys()
    
    def values(self):
        return {}.values()

    def items(self):
        return {}.items()

    def get(self, key, default=None):
        return default

    def clear(self):
        return None

    ##################################################################
    ## OTHER PROPERTIES AND METHODS

    @property
    def as_dict(self):
        return {}

    @property
    def parent(self):
        """the null kvs is its own parent (to allow for parent.parent.parent... chains)"""
        return self

    @property
    def height(self):
        """the null kvs is at height zero"""
        return 0
        
    ##################################################################
    ## GLOBAL METHODS

    @classmethod
    def kvs_exists(cls, namespace):
        return True

    @classmethod
    def kvs_get(cls, namespace=None, create_if_not_exist=True):
        return cls()

    @classmethod
    def kvs_update(cls, namespace=None, dct=None, action_if_exists=None):
        raise RuntimeError("can't set items in the null value store")

    @classmethod
    def kvs_delete(namespace):
        return None

        
###########################################################################################
## KEY VALUE STORE
class KeyValueStore(KeyValueStoreBase, models.Model):
    """
    a model that implements a key-value storage (it mostly behaves like a dict)
    
    NOTE
    - this model contains only the information about the namespace in which
        the key-value pairs exist
    - however, most of the functionality is actually attached to this model,
        not to the bona fide storage model `KeyValuePairs`
    - when we refer to a storage segment we mean all the key value pairs that share
        a given namespace
    """
    _namespace = models.CharField(max_length=255, unique=True, blank=True, default="", null=False)
        # the name of this particular namespace

    @property
    def namespace(self):
        return self._namespace

    ##################################################################
    ## BACKEND METHODS
        
        ## NOTE: those are the only methods that interface with the storage backend
        ## to the extent that that those can be moved over to another backend, those
        ## are the only methods that need to be changed when switching backends

    @property
    def _all_items(self):
        """
        backend method: retrieve all items in this segment
        """
        return self.keyvaluepair_set.all()
        
    def _item(self, key):
        """
        backend method: retrieve one items in this segment
        """
        return self.keyvaluepair_set.get(key=key)
        
    def _create_item(self, key, value):
        """
        backend method: create one item in this segment
        """
        KeyValuePair.objects.create(segment=self, key=key, value=value)

    @classmethod
    def _kvs_retrieve(cls, namespace):
        """
        backend method: read an existing segment object
        """
        return cls.objects.get(_namespace=namespace)
        
    @classmethod
    def _kvs_create(cls, namespace):
        """
        backend method: create a new segment object
        """
        new_segment = cls(_namespace=namespace)
        new_segment.save()
        return new_segment
        
        
    ##################################################################
    ## DICT INTERFACE PROPERTIES AND METHODS

    def __str__(self):
        return "<KeyValStore '{0.name}'>".format(self)

    def __getitem__(self, key):
        """
        returns the value associated with the selected key in this storage segment (or parents)
        """
        try: item = self._item(key)
        except:
            if self._parent == None: raise KeyError()
            else: return self.parent.__getitem__(key)
                # if item does not exist and there is a parent: get it from parent 
        return item.value

    def __setitem__(self, key, value):
        """
        sets the value of the given key in this storage segment (not: in parent)
        """
        try: item = self._item(key)
        except: self._create_item(key, value)
        else:
            item.value = value
            item.save()

    def __delitem__(self, key):
        """
        removes the given key/value pair from this storage segment (not: from parent)
        """
        try: item = self._item(key)
        except KeyValuePair.DoesNotExist: raise KeyError
        else: item.delete()

    def __contains__(self, key):
        """
        checks whether key exists in this storage segment (or parents)
        """
        try: self._item(key)
        except KeyValuePair.DoesNotExist: 
            if self._parent != None: return self.parent.__contains__(key)
            else: return False
        return True

    def __len__(self):
        """
        returns the length of this storage segment (including parents)
        """
        this = self._all_items.count()
        if self._parent == None: return this
        return this + len(self.parent)
            
    def keys(self):
        """
        returns an iterator for the keys in this storage segment (including parents)
        """
        this = (  item.key for item in self._all_items  )
        if self._parent == None: return this
        parents = self.parent.keys()
        return chain(this, parents)
            
    def values(self):
        """
        returns an iterator over the values in this storage segment (including parents)
        """
        this = (  item.value for item in self._all_items  )
        if self._parent == None: return this
        parents = self.parent.values()
        return chain(this, parents)
    
    def items(self):
        """
        returns an iterator over the key-value pairs in this storage segment (including parents)
        """
        this = (  (item.key, item.value) for item in self._all_items  )
        if self._parent == None: return this
        parents = self.parent.items()
        return chain(this, parents)
    
    def clear(self):
        """
        deletes all keys value pairs in this storage segment (not: in parent)
        """
        self._all_items.delete()

    def __repr__(self):
        """
        returns a representation of the storage in this storage segment (not: in parent)
        """
        return str(self.as_dict)


    ##################################################################
    ## OTHER PROPERTIES AND METHODS

    @property
    def as_dict(self):
        """
        gets a python dictionary that represents this storage segment (including parents)

        NOTE: this dictionary is not linked to the key value storage, it is only a snapshot!
        """
        this = {item.key : item.value for item in self._all_items}
        if self._parent == None: return this
        else: 
            parents = self.parent.as_dict
            this.update(parents)
            return this

    ##################################################################
    ## GLOBAL METHODS
    
    ## KVS EXISTS
    @classmethod
    def kvs_exists(cls, namespace):
        """
        determines whether this namespace already exists in the key-value storage
        """
        if namespace==None: namespace=""
        try: cls._kvs_retrieve(namespace)
        except: return False
        return True


    ## KVS GET
    @classmethod
    def kvs_get(cls, namespace=None, hierarchy_separator=None, create_if_not_exist=True):
        """
        gets the key value store associated to `namespace`, possibly creating it

        NOTES
        - if `namespace`==None, the default (="") namespace is used
        - if the particular namespace does not exist it is created, provided that `create_if_not_exist`
            is true'ish (otherwise it raises an exception)
        - if `hierarchy_separator` is None the namespace will not have any parents; if it is a string,
            then this string is used to separate hierarchies in the namespace; if it is True, the default
            hierarchy separator "::" is used
        """
        if namespace == None: namespace = ""
        if hierarchy_separator == True: hierarchy_separator='::'

        try: kvs = cls._kvs_retrieve(namespace)
        except:
            if not create_if_not_exist: raise
            kvs = cls._kvs_create(namespace)
        
        if not hierarchy_separator: kvs._parent = None
        else:
            parent_namespace = cls.parent_namespace(namespace, hierarchy_separator)
            if parent_namespace == None: kvs._parent = None
            else: kvs._parent = cls.kvs_get(parent_namespace, hierarchy_separator, create_if_not_exist)
        
        return kvs
        
    ## KVS UPDATE
    @classmethod
    def kvs_update(cls, namespace=None, dct=None, action_if_exists=None):
        """
        creates/updates the key-value storage in a given namespace
        
        NOTES
        - __repr__ returns output that is using this function, allowing to create the namespace
        - if a key value store under `namespace` does not exist it is created
        - if it does exist, it
            depends on `action_if_exist` what happens
            -- RAISE: raise an exception
            -- CLEAR: clear the current contents, and add the new contents from `dct`
            -- UPDATE: update the current contents from `dct` (`dct` wins)
        """
        if namespace==None: namespace=""
        if dct==None: dct={}
        if action_if_exists==None: action_if_exists=cls.RAISE
        if cls.kvs_exists(namespace):
            if   action_if_exists == cls.RAISE: raise RuntimeError("namespace {} already exists".format(namespace))
            elif action_if_exists == cls.CLEAR: cls.kvs_get(namespace).clear()
        kvs = cls.kvs_get(namespace)
        for key in dct:
            kvs[key] = dct[key]
        return kvs


    ## KVS DELETE   
    @classmethod
    def kvs_delete(cls, namespace):
        """deletes the key-value storage under a given namespace"""
        if namespace==None: namespace=""
        try: kvs = cls._kvs_retrieve(namespace)
        except: return 
        kvs.delete()
        


###########################################################################################
## KEY VALUE PAIR
class KeyValuePair(models.Model):
    """
    stores the actual key-value pairs, and a reference to the namespace
    """
    segment = models.ForeignKey(KeyValueStore, on_delete=models.CASCADE, blank=True, null=False, db_index=True)
        # namespace
        
    key = models.CharField(max_length=240, blank=False, null=False, db_index=True)
        # key (unique in this namespace--enforced?)
        
    value = models.CharField(max_length=240, blank=True, null=True, db_index=True)
        # value associate to this key