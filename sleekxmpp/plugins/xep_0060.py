from __future__ import with_statement
import base
import logging
from xml.etree import cElementTree as ET

class xep_0060(base.base_plugin):
	"""
	XEP-0060 Publish Subscribe
	"""

	def plugin_init(self):
		self.xep = '0060'
		self.description = 'Publish-Subscribe'
	
	def create_node(self, jid, node, config=None, collection=False):
		pubsub = ET.Element('{http://jabber.org/protocol/pubsub}pubsub')
		create = ET.Element('create')
		create.set('node', node)
		pubsub.append(create)
		configure = ET.Element('configure')
		if collection:
			if config is None:
				collectform = self.xmpp.plugin['xep_0004'].makeForm('submit')
			else:
				collectform = config
			if collectform.field.has_key('FORM_TYPE'):
				collectform.field['FORM_TYPE'].setValue('http://jabber.org/protocol/pubsub#node_config')
			else:
				collectform.addField('FORM_TYPE', 'hidden', value='http://jabber.org/protocol/pubsub#node_config')
			if collectform.field.has_key('pubsub#node_type'):
				collectform.field['pubsub#node_type'].setValue('collection')
			else:
				collectform.addField('pubsub#node_type', value='collection')
			configure.append(collectform.getXML('submit'))
		elif config is not None:
			configure.append(config.getXML('submit'))
		pubsub.append(configure)
		iq = self.xmpp.makeIqSet(pubsub)
		iq.attrib['to'] = jid
		iq.attrib['from'] = self.xmpp.fulljid
		id = iq.get('id')
		#self.xmpp.add_handler("<iq id='%s'/>" % id, self.handlerCreateNodeResponse)
		result = self.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result is False or result is None or result.get('type') == 'error': return False
		return True
	
	def subscribe(self, jid, node, bare=True, subscribee=None):
		pubsub = ET.Element('{http://jabber.org/protocol/pubsub}pubsub')
		subscribe = ET.Element('subscribe')
		subscribe.attrib['node'] = node
		if subscribee is None:
			if bare:
				subscribe.attrib['jid'] = self.xmpp.jid
			else:
				subscribe.attrib['jid'] = self.xmpp.fulljid
		else:
			subscribe.attrib['jid'] = subscribee
		pubsub.append(subscribe)
		iq = self.xmpp.makeIqSet(pubsub)
		iq.attrib['to'] = jid
		iq.attrib['from'] = self.xmpp.fulljid
		id = iq.get('id')
		result = self.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result is False or result is None or result.get('type') == 'error': return False
		return True
	
	def unsubscribe(self, jid, node, bare=True, subscribee=None):
		pubsub = ET.Element('{http://jabber.org/protocol/pubsub}pubsub')
		unsubscribe = ET.Element('unsubscribe')
		unsubscribe.attrib['node'] = node
		if subscribee is None:
			if bare:
				unsubscribe.attrib['jid'] = self.xmpp.jid
			else:
				unsubscribe.attrib['jid'] = self.xmpp.fulljid
		else:
			unsubscribe.attrib['jid'] = subscribee
		pubsub.append(unsubscribe)
		iq = self.xmpp.makeIqSet(pubsub)
		iq.attrib['to'] = jid
		iq.attrib['from'] = self.xmpp.fulljid
		id = iq.get('id')
		result = self.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result is False or result is None or result.get('type') == 'error': return False
		return True
	
	def getNodeConfig(self, jid, node=None): # if no node, then grab default
		pubsub = ET.Element('{http://jabber.org/protocol/pubsub#owner}pubsub')
		if node is not None:
			configure = ET.Element('configure')
			configure.attrib['node'] = node
		else:
			configure = ET.Element('default')
		pubsub.append(configure)
		#TODO: Add configure support.
		iq = self.xmpp.makeIqGet()
		iq.append(pubsub)
		iq.attrib['to'] = jid
		iq.attrib['from'] = self.xmpp.fulljid
		id = iq.get('id')
		#self.xmpp.add_handler("<iq id='%s'/>" % id, self.handlerCreateNodeResponse)
		result = self.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result is None or result == False or result.get('type') == 'error':
			logging.warning("got error instead of config")
			return False
		if node is not None:
			form = result.find('{http://jabber.org/protocol/pubsub#owner}pubsub/{http://jabber.org/protocol/pubsub#owner}configure/{jabber:x:data}x')
		else:
			form = result.find('{http://jabber.org/protocol/pubsub#owner}pubsub/{http://jabber.org/protocol/pubsub#owner}default/{jabber:x:data}x')
		if not form or form is None:
			logging.error("No form found.")
			return False
		return self.xmpp.plugin['xep_0004'].buildForm(form)
	
	def deleteNode(self, jid, node):
		pubsub = ET.Element('{http://jabber.org/protocol/pubsub#owner}pubsub')
		iq = self.xmpp.makeIqSet()
		delete = ET.Element('delete')
		delete.attrib['node'] = node
		pubsub.append(delete)
		iq.append(pubsub)
		iq.attrib['to'] = jid
		iq.attrib['from'] = self.xmpp.fulljid
		id = iq.get('id')
		result = self.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result is not None and result is not False and result.attrib.get('type', 'error') != 'error':
			return True
		else:
			return False
		
	
	def setNodeConfig(self, jid, node, config):
		pubsub = ET.Element('{http://jabber.org/protocol/pubsub#owner}pubsub')
		configure = ET.Element('configure')
		configure.attrib['node'] = node
		config = config.getXML('submit')
		configure.append(config)
		pubsub.append(configure)
		iq = self.xmpp.makeIqSet(pubsub)
		iq.attrib['to'] = jid
		iq.attrib['from'] = self.xmpp.fulljid
		id = iq.get('id')
		result = self.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result is None or result.get('type') == 'error': 
			return False
		return True
	
	def setItem(self, jid, node, items={}):
		pubsub = ET.Element('{http://jabber.org/protocol/pubsub}pubsub')
		publish = ET.Element('publish')
		publish.attrib['node'] = node
		for id in items:
			item = ET.Element('item')
			if id is not None:
				item.attrib['id'] = id
			item.append(items[id])
			publish.append(item)
		pubsub.append(publish)
		iq = self.xmpp.makeIqSet(pubsub)
		iq.attrib['to'] = jid
		iq.attrib['from'] = self.xmpp.fulljid
		id = iq.get('id')
		result = self.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result is None or result is False or result.get('type') == 'error': return False
		return True
	
	def deleteItem(self, jid, node, item):
		pubsub = ET.Element('{http://jabber.org/protocol/pubsub}pubsub')
		retract = ET.Element('retract')
		retract.attrib['node'] = node
		itemn = ET.Element('item')
		itemn.attrib['id'] = item
		retract.append(itemn)
		pubsub.append(retract)
		iq = self.xmpp.makeIqSet(pubsub)
		iq.attrib['to'] = jid
		iq.attrib['from'] = self.xmpp.fulljid
		id = iq.get('id')
		result = self.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result is None or result is False or result.get('type') == 'error': return False
		return True
	
	def addItem(self, jid, node, items={}):
		return setItem(jid, node, items)
	
	def getNodes(self, jid):
		response = self.xmpp.plugin['xep_0030'].getItems(jid)
		items = response.findall('{http://jabber.org/protocol/disco#items}query/{http://jabber.org/protocol/disco#items}item')
		nodes = {}
		if items is not None and items is not False:
			for item in items:
				nodes[item.get('node')] = item.get('name')
		return nodes
	
	def getItems(self, jid, node):
		response = self.xmpp.plugin['xep_0030'].getItems(jid, node)
		items = response.findall('{http://jabber.org/protocol/disco#items}query/{http://jabber.org/protocol/disco#items}item')
		nodeitems = []
		if items is not None and items is not False:
			for item in items:
				nodeitems.append(item.get('node'))
		return nodeitems
	
	def modifyAffiliation(self, ps_jid, node, user_jid, affiliation):
		if affiliation not in ('owner', 'publisher', 'member', 'none', 'outcast'):
			raise TypeError
		pubsub = ET.Element('{http://jabber.org/protocol/pubsub#owner}pubsub')
		affs = ET.Element('affiliations')
		affs.attrib['node'] = node
		aff = ET.Element('affiliation')
		aff.attrib['jid'] = user_jid
		aff.attrib['affiliation'] = affiliation
		affs.append(aff)
		pubsub.append(affs)
		iq = self.xmpp.makeIqSet(pubsub)
		iq.attrib['to'] = ps_jid
		iq.attrib['from'] = self.xmpp.fulljid
		id = iq.get('id')
		result = self.xmpp.send(iq, "<iq id='%s'/>" % id)
		if result is None or result is False or result.get('type') == 'error': return False
		return True
	
	def addNodeToCollection(self, jid, child, parent=''):
		config = self.getNodeConfig(jid, child)
		if not config or config is None:
			self.lasterror = "Config Error"
			return False
		try:
			config.field['pubsub#collection'].setValue(parent)
		except KeyError:
			logging.warning("pubsub#collection doesn't exist in config, trying to add it")
			config.addField('pubsub#collection', value=parent)
		if not self.setNodeConfig(jid, child, config):
			return False
		return True
	
	def removeNodeFromCollection(self, jid, child):
		self.addNodeToCollection(jid, child, '')
