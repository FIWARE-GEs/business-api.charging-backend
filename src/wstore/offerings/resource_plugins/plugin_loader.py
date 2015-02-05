# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of WStore.

# WStore is free software: you can redistribute it and/or modify
# it under the terms of the European Union Public Licence (EUPL)
# as published by the European Commission, either version 1.1
# of the License, or (at your option) any later version.

# WStore is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# European Union Public Licence for more details.

# You should have received a copy of the European Union Public Licence
# along with WStore.
# If not, see <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>.


from __future__ import unicode_literals

import os
import json
import zipfile

from django.conf import settings

from wstore.offerings.resource_plugins.plugin_manager import PluginManager
from wstore.offerings.resource_plugins.plugin_error import PluginError
from wstore.offerings.resource_plugins.plugin_rollback import installPluginRollback

class PluginLoader():

    _plugin_manager = None

    def __init__(self):
        self._plugin_manager = PluginManager.get_instance()
        self._plugins_path = os.path.join(settings.BASEDIR, 'wstore')
        self._plugins_path = os.path.join(self._plugins_path, 'offerings')
        self._plugins_path =  os.path.join(self._plugins_path, 'resource_plugins')
        self._plugins_path =  os.path.join(self._plugins_path, 'plugins')

    @installPluginRollback
    def install_plugin(self, path):

        # Validate package file
        if not zipfile.is_zipfile(path):
            raise PluginError('Invalid package format')

        # Uncompress plugin file
        with zipfile.ZipFile(path, 'r') as z:

            # Validate that the file package.json exists
            if not 'package.json' in z.namelist():
                raise PluginError('Missing package.json file')

            # Read package metainfo
            json_file = z.read('package.json')
            try:
                json_info = json.loads(json_file)
            except:
                raise PluginError('Invalid format in package.json file. JSON cannot be parsed')

            # Create a directory for the plugin
            ## Check plugin name
            if not 'name' in json_info:
                raise PluginError('Invalid format in package.json file. Missing name field')

            dir_name = json_info['name'].replace(' ', '_')

            ## Check if the directory already exists
            plugin_path = os.path.join(self._plugins_path, dir_name)
            if os.path.isdir(plugin_path):
                raise PluginError('A plugin with the same name already exists')

            ## Create the directory
            os.mkdir(plugin_path)

            # Extrat files
            z.extractall(plugin_path)

        # Load plugin
        self._plugin_manager.register_plugin(json_info)

    def uninstall_plugin(self):
        # Unload plugin
        # Remove plugin files
        pass

    def _load_plugin(self):
        # Read configuration file
        plugin_info = {}
        # Call register plugin method
        self._plugin_manager.register_plugin(plugin_info)

    def load_plugins(self):
        pass