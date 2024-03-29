"""
    .py - A plugin for pinging Jids.
    Copyright (C) 2008 Nathan Fritz

    SleekBot is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    SleekBot is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this software; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import logging
from xml.etree import cElementTree as ET

class pubsub_browser(object):
	def __init__(self, bot, config):
		self.bot = bot
		self.config = config
		self.psserver = config.get('server', self.bot.server)
		self.about = "Create and configure nodes, leafs, and add items."
		self.pubsub = self.bot.plugin['xep_0060']
		self.xform = self.bot.plugin['xep_0004']
		self.adhoc = self.bot.plugin['xep_0050']
		
		createleaf = self.bot.plugin['xep_0004'].makeForm('form', "Create Leaf")
		createleaf.addField('node', 'text-single')
		self.bot.plugin['xep_0050'].addCommand('newleaf', 'Create Leaf', createleaf, self.createLeafHandler, True)

		createcollect = self.bot.plugin['xep_0004'].makeForm('form', "Create Collection")
		createcollect.addField('node', 'text-single', 'Node name')
		self.bot.plugin['xep_0050'].addCommand('newcollection', 'Create Collection', createcollect, self.createCollectionHandler, True)

		setitem = self.bot.plugin['xep_0004'].makeForm('form', "Set Item")
		setitem.addField('node', 'text-single')
		setitem.addField('id', 'text-single')
		setitem.addField('xml', 'text-multi')
		self.bot.plugin['xep_0050'].addCommand('setitem', 'Set Item', setitem, self.setItemHandler, True)

		remitem = self.bot.plugin['xep_0004'].makeForm('form', "Retract Item")
		remitem.addField('node', 'text-single', 'Node name')
		remitem.addField('id', 'text-single')
		self.bot.plugin['xep_0050'].addCommand('remitem', 'Retract Item', remitem, self.retractItemHandler, True)

		
		confnode = self.bot.plugin['xep_0004'].makeForm('form', "Configure Node")
		confnode.addField('node', 'text-single')
		self.bot.plugin['xep_0050'].addCommand('confnode', 'Configure Node', confnode, self.updateConfigHandler, True)
		
		subnode = self.bot.plugin['xep_0004'].makeForm('form', "Subscribe Node")
		subnode.addField('node', 'text-single')
		self.bot.plugin['xep_0050'].addCommand('subnode', 'Subscribe Node', subnode, self.subscribeNodeHandler, True)
	
		affiliation = self.bot.plugin['xep_0004'].makeForm('form', "Change Affiliation")
		affiliation.addField('node', 'text-single', 'Node name')
		affiliation.addField('jid', 'text-single')
		affs = affiliation.addField('affiliation', 'list-single', 'Affilation')
		affs_list = ('owner', 'publisher', 'member', 'none', 'outcast')
		for aff in affs_list:
			affs.addOption(aff, aff.title())
		self.bot.plugin['xep_0050'].addCommand('affiliation', 'Change Affiliation', affiliation, self.setAffiliation, True)
		
	def getStatusForm(self, title, msg):
		status = self.xform.makeForm('form', title)
		status.addField('done', 'fixed', value=msg)
		return status

	def createLeafHandler(self, form, sessid):
		value = form.getValues()
		node = value.get('node')
		self.adhoc.sessions[sessid]['pubsubnode'] = node
		nodeform = self.pubsub.getNodeConfig(self.psserver)
		logging.debug("nodeform: %s" % nodeform)
		if nodeform:
			return nodeform, self.createLeafHandlerSubmit, True
		else:
		#if True:
			if self.bot.plugin['xep_0060'].create_node(self.psserver, self.adhoc.sessions[sessid]['pubsubnode']):
				return self.getStatusForm('Error', "Unable to retrieve default node configuration.\nNode without configuration was created instead."), None, False
			return self.getStatusForm('Error', "Unable to retrieve default node configuration.\nFurthermore, creating a node without a configuration failed."), None, False
	
	def createLeafHandlerSubmit(self, form, sessid):
		if not self.bot.plugin['xep_0060'].create_node(self.psserver, self.adhoc.sessions[sessid]['pubsubnode'], form):
			return self.getStatusForm('Error', "Could not create node."), None, False
		else:
			return self.getStatusForm('Done', "Node %s created." % self.adhoc.sessions[sessid]['pubsubnode']), None, False
	
	def createCollectionHandler(self, form, sessid):
		value = form.getValues()
		node = value.get('node')
		self.adhoc.sessions[sessid]['pubsubnode'] = node
		self.bot.plugin['xep_0060'].create_node(self.psserver, node, collection=True)
		nodeform = self.pubsub.getNodeConfig(self.psserver, node)
		if nodeform:
			return nodeform, self.updateConfigHandler, True
	
	def subscribeNodeHandler(self, form, sessid):
		value = form.getValues()
		node = value.get('node')
		if self.pubsub.subscribe(self.psserver, node):
			return self.getStatusForm('Done', "Subscribed to node %s." % node), None, False
		return self.getStatusForm('Error', "Could not subscribe to %s." % node), None, False
	
	def updateConfigHandler(self, form, sessid):
		value = form.getValues()
		node = value.get('node')
		self.adhoc.sessions[sessid]['pubsubnode'] = node
		nodeform = self.pubsub.getNodeConfig(self.psserver, node)
		if nodeform:
			return nodeform, self.updateConfigHandlerSubmit, True
		else:
			return self.getStatusForm('Error', 'Unable to retrieve node configuration.'), None, False
	
	def updateConfigHandlerSubmit(self, form, sessid):
		node = self.adhoc.sessions[sessid]['pubsubnode']
		self.pubsub.setNodeConfig(self.psserver, node, form)
		return self.getStatusForm('Done', "Updated node %s." % node), None, False
	
	
	def setItemHandler(self, form, sessid):
		value = form.getValues()
		self.pubsub.setItem(self.psserver, value['node'], {value['id']: ET.fromstring(value['xml'])})
		done = self.xform.makeForm('form', "Finished")
		done.addField('done', 'fixed', value="Published Item.")
		return done, None, False
	
	def retractItemHandler(self, form, sessid):
		value = form.getValues()
		self.pubsub.deleteItem(self.psserver, value['node'], value['id'])
		done = self.xform.makeForm('form', "Finished")
		done.addField('done', 'fixed', value="Retracted Item.")
		return done, None, False
	
	def setAffiliation(self, form, sessid):
		value = form.getValues()
		self.pubsub.modifyAffiliation(self.psserver, value['node'], value['jid'], value['affiliation'])
		done = self.xform.makeForm('form', "Finished")
		done.addField('done', 'fixed', value="Updated Affiliation.")
		return done, None, False
