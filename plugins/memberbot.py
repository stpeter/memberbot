# -*- coding: utf-8 -*-
"""
    memberbot.py - A script that enables XSF members to vote on official 
    XSF business. 
    Based on memberbot.py by Peter Saint-Andre (stpeter@jabber.org)
    Copyright (C) 2008 Mateusz Biliński (mateusz@bilinski.it)

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
import os.path
import glob
import random
from string import find

from xml.dom.minidom import parse,Document

class memberbot(object):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.about = '''Memberbot enables JSF members to vote on official JSF business.
Based on memberbot.py by Peter Saint-Andre.
Written by: Mateusz Biliński'''
        self.initDone = False
        self.bot.add_event_handler('message', self.handle_message_event, threaded=True)
        self.bot.add_event_handler("got_online", self.got_online)
        self._set_responses()

    def got_online(self, event):
        '''
	Basically this initializes Memberbot data when bot gets online.

	Based mainly on memberbot.py by stpeter.
	'''	

        if not self.initDone:
        ## survey data initialization from memberbot.py by stpeter
            self._init_data()
            self._read_questions_from_survey_file()
            self._init_survey_based_on_type()
            self._handleSurvey()
            self._init_survey_data_for_jids_in_roster()
            self.initDone = True

    def _init_data(self):
        ## variables from memberbot.py by stpeter
        self.surveyDir = self.config.find('survey').attrib['dir']
        self.surveyFile = self.config.find('survey').attrib['file']
        self.tracker = {}
        self.answers = []
        self.questions = []
        self.votecounter = {}
        self.boardcounter = {}
        self.councilcounter = {}
        self.businesscounter = {}
        self.surveyOrder = {}
        self.boardCouncilQuestionsOrder = {}

        self.questArray = {}
        self.appNames = {}
        self.boardArray = {}
        self.councilArray = {}
        self.businessArray = {}

        ## this is a hack for JSF board and council elections!
        self.maxBoard = 5
        self.maxCouncil = 5

        ## survey data
        self.numberOfItems = 0
        self.numQuest = 0
        self.numApp = 0
        self.numCand = 0
        self.numBoard = 0
        self.numCouncil = 0
        self.numBusiness = 0
        self.boardLeft = 0
        self.councilLeft = 0
        self.surveyType = ''
        self.initialResponse = ''

    def _send_test_form(self, jid):
        form = self.bot.plugin['xep_0004'].makeForm('form', 'Test Form', 'Please fill me out!')
        form.addField('crap', label='Fill in some crap')
        form.field['crap'].require()
        self.bot.send(form.getXMLMessage(jid))


    def _read_questions_from_survey_file(self):
        '''Read survey data from file in way that memberbot.py by stpeter does it'''
        theseQuestions = parse(self.surveyFile)
        self.mainQuestNode = (theseQuestions.getElementsByTagName("questions")[0])
        meetingNode =  (theseQuestions.getElementsByTagName("meeting")[0])
        meetingDateNode = (meetingNode.getElementsByTagName("date")[0])
        self.meetingDate = self._getText(meetingDateNode.childNodes)

    def _getText(self, nodelist):
        '''Helper method from memberbot.py by stpeter.'''
        thisText = ""
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                thisText = thisText + node.data
        return thisText    

    def _init_survey_data_for_jids_in_roster(self):
        '''Init survey data per JID in way that memberbot.py by stpeter does it'''

        for jid in self.bot.roster:
            #logging.debug('got another jid!')
            #thisJID = jid.getStripped()s
            #logging.debug(thisJID + ' is in roster!')
            self.tracker[jid] = 0
            ## we want a dictionary with JID as the key
            ## for each JID, we will have a list of answer values

            self.boardcounter[jid] = 0
            self.councilcounter[jid] = 0
            self.businesscounter[jid] = 0

        for jid in self.bot.roster:
            self.votecounter[jid] = ['' for i in range(self.numberOfItems)]
        #if self.surveyType == 'yesno':
            #for jid in self.bot.roster:
                #self.votecounter[jid] = ['' for i in range(self.numberOfItems)]
        #elif self.surveyType == 'boardcouncil':
            #for jid in self.bot.roster:
                #self.votecounter[jid] = []

    def _set_random_questions_order_for_jid(self, jid):
        if self.surveyType == "yesno":
            questions_numbers = range(self.numberOfItems)
            random.shuffle(questions_numbers)
            self.surveyOrder[jid] = questions_numbers
        elif self.surveyType == "boardcouncil":
            board_questions_numbers = range(self.numBoard)
            random.shuffle(board_questions_numbers)
            council_questions_numbers = range(self.numBoard, self.numberOfItems)
            random.shuffle(council_questions_numbers)
            self.boardCouncilQuestionsOrder[jid] = board_questions_numbers + council_questions_numbers

    def _init_survey_based_on_type(self):
        '''Survey init based on survey type (from memberbot.py by stpeter).'''
        typeText = self.mainQuestNode.attributes["type"]
        self.surveyType = typeText.value
        #logging.debug("SURVEY TYPE IS " + str(self.surveyType))

        ### handling simple yes or no questions ###

        if self.surveyType == "yesno":
            for question in self.mainQuestNode.getElementsByTagName("question"):
                self.numQuest = self.numQuest + 1
            self.numberOfItems = self.numQuest
            allItems = range(self.numQuest)
            for i in allItems:
                self.questArray[i] = ''
            self.initialResponse = self.responses['yesno_initial_response'] % { 'numQuest' : self.numQuest }

        ### accepting new JSF members ###

        elif self.surveyType == "acceptmembers":
            for applicant in self.mainQuestNode.getElementsByTagName("applicant"):
                self.numApp = self.numApp + 1
            self.numberOfItems = self.numApp
            allItems = range(self.numApp)
            for i in allItems:
                self.appNames[i] = ''
            self.initialResponse = self.responses['acceptmembers_initial_response'] % { 'numApp' : self.numApp }

        ### electing new people to the Board and the Council ###

        elif self.surveyType == "boardcouncil":
            # count candidates and initialize array
            for item in self.mainQuestNode.getElementsByTagName("item"):
                candNode = (self.mainQuestNode.getElementsByTagName("item")[self.numCand])
                self.numCand = self.numCand + 1
                candType = ''
                candText = candNode.attributes["type"]
                candType = candText.value
                #logging.debug("CANDIDATE TYPE IS " + str(candType))
                if (candType == 'board'):
                    self.numBoard = self.numBoard + 1
                    #logging.debug("NUM BOARD IS NOW " + str(self.numBoard))
                elif (candType == 'council'):
                    self.numCouncil = self.numCouncil + 1
                    #logging.debug("NUM COUNCIL IS NOW " + str(self.numCouncil))
                elif (candType == 'otherbusiness'):
                    self.numBusiness = self.numBusiness + 1
                    #logging.debug("NUM BUSINESS IS NOW " + str(self.numBusiness))
            self.numberOfItems = self.numBoard + self.numCouncil + self.numBusiness
            allItems = range(self.numberOfItems)
            for i in allItems:
                self.questArray[i] = ''
            #logging.debug("number of items is " + str(self.numberOfItems))
            #logging.debug("number of candidates is " + str(self.numCand))
            #logging.debug("number for Board is " + str(self.numBoard))
            #logging.debug("number for Council is " + str(self.numCouncil))
            #logging.debug("NUM BUSINESS IS " + str(self.numBusiness))
            #numberOfItems = numCand + numBusiness
            allBoard = range(self.numBoard)
            for i in allBoard:
                self.boardArray[i] = ''
            allCouncil = range(self.numCouncil)
            for i in allCouncil:
                self.councilArray[i] = ''
            allBusiness = range(self.numBusiness)
            for i in allBusiness:
                self.businessArray[i] = ''
            # initial response differs depending on whether there are other matters to vote on...
            if self.numBusiness == 0:
                self.initialResponse = self.responses['boardcouncil_initial_response_2parts'] % { 'numBoard' : self.numBoard,
                                                                                                  'maxBoard' : self.maxBoard,
                                                                                                  'numCouncil' : self.numCouncil,
                                                                                                  'maxCouncil' : self.maxCouncil,
                                                                                                  'meetingDate' : self.meetingDate}
            else:
                self.initialResponse = self.responses['boardcouncil_initial_response_3parts'] % { 'numBoard' : self.numBoard,
                                                                                                  'maxBoard' : self.maxBoard,
                                                                                                  'numCouncil' : self.numCouncil,
                                                                                                  'maxCouncil' : self.maxCouncil,
                                                                                                  'numBusiness' : self.numBusiness,
                                                                                                  'meetingDate' : self.meetingDate}
        else:
            # no survey type!
            logging.debug("NO SURVEY TYPE!")

    def handle_message_event(self, msg):
        '''Called when a message is received'''
        if self.initDone:
            personflag = 'no'
            #inFrom = msg['from']
            inMsg = msg['message']
            #logging.debug('got message from: ' + inFrom)
            #logging.debug('message is: ' + inMsg + '')
            ## strip the resource off the from attribute
            #bits = split(inFrom, '@')
            #inNode = bits[0]
            #logging.debug('IN NODE IS: ' + inNode + '')
            #inRest = bits[1]
            #logging.debug('IN REST IS: ' + inRest + '')
            #inDomain, inResource = split(inRest, '/', 1)
            #logging.debug('IN DOMAIN IS: ' + inDomain + '')
            #logging.debug('IN RESOURCE IS: ' + inResource + '')
            #slash_ind = find(inRest, '/')
            #inDomain = inRest[:slash_ind]
            #inResource = inRest[(slash_ind + 1):]
            #logging.debug('IN DOMAIN IS: ' + inDomain + '')
            #logging.debug('IN RESOURCE IS: ' + inResource + '')
            #inJID = inNode + '@' + inDomain
            thisJID = ''
            inJID = msg['jid']
            logging.debug('inJID is ' + inJID)
            ## check to see if this message is from someone we know
            if inJID in self.bot.roster:
                logging.debug('got a message from someone in the roster!')
                thisJID = inJID
                logging.debug('that person is ' + thisJID)
                personflag = 'yes'
            else:
                logging.debug('got a message from someone not in the roster')
                logging.debug('that person is ' + inJID)
            #for jid in myJIDs:
                #checkJID = jid.getStripped()
                #logging.debug('the JID we are checking is ' + checkJID)
                #if inJID == checkJID:
                    #logging.debug('got a message from someone in the roster!')
                    #thisJID = inJID
                    #logging.debug('that person is ' + thisJID)
                    #personflag = 'yes'
                #else:
                    #pass
            #logging.debug('thisJID is ' + thisJID)
            #logging.debug('personflag is : ' + personflag)
            msgText = self.responses['default_msg']
            msgType = 'chat'
            ## only chat with people who are in our roster
            if (personflag == 'yes'):
                ## check if they've already completed the survey
                respflag = 0
                ## look on the filesystem for xml files
                placeToLook = self.surveyDir + '*'
                respList = glob.glob(placeToLook)
                #logging.debug('has this person already completed the survey?')
                for x in respList:
                    # vTODO: this should be done using os.path module
                    slash = find(x, '/')
                    fileJID = x[(slash + 1):]
                    checkerJID = thisJID + '.xml'
                    #logging.debug('checking... ' + fileJID)
                    #logging.debug('checking against... ' + checkerJID)
                    if (fileJID == checkerJID):
                        respflag = respflag + 1
                if (respflag > 0):
                    msgText = self.responses['already_completed_msg']
                else:
                    logging.debug("tracker is " + str(self.tracker[thisJID]))
                    logging.debug("number of questions is " + str(self.numberOfItems))
                    if (self.tracker[thisJID] == 0):
                        #logging.debug("handling initial inquiry, tracker is zero")
                        if (inMsg == 'yes'):
                            msgText = self.initialResponse
                        elif (inMsg == 'ok'):
                            self._set_random_questions_order_for_jid(thisJID)

                            if (self.surveyType == 'boardcouncil'):
                                #logging.debug("Board and Council vote")
                                thisQuestion = self.questions[self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]]]
                                #thisQuestion = self.questions[self.tracker[thisJID]]
                                msgText = self.responses['boardcouncil_vote_msg'] % { 'candidateNum' : self.tracker[thisJID] + 1,
                                                                                      'question' : thisQuestion }
                            elif (self.surveyType == 'yesno'):
                                #logging.debug("simple yes/no vote")
                                thisQuestion = self.questions[self.surveyOrder[thisJID][self.tracker[thisJID]]]
                                msgText = self.responses['yesno_vote_msg'] % { 'questionNum' : self.tracker[thisJID] + 1,
                                                                               'question' : thisQuestion }
                            else:
                                #logging.debug("membership application vote")
                                msgText = self.responses['yesno_vote_msg'] % { 'applicationNum' : self.tracker[thisJID] + 1,
                                                                               'question' : thisQuestion }
                            self.tracker[thisJID] = self.tracker[thisJID] + 1
                            #logging.debug("OK, THE TRACKER IS NOW " + str(self.tracker[thisJID]))
                        elif (inMsg == 'no'):
                            msgText = self.responses['ok_bye_msg']
                        else:
                            msgText = self.responses['would_vote_msg']
                    elif (self.tracker[thisJID] < self.numberOfItems):
                        #logging.debug("handling a vote, tracker is greater than zero")
                        if ((inMsg == 'yes') or (inMsg == 'no')):
                            ## handle the vote
                            if (self.surveyType == 'boardcouncil'):
                                boardNum = self.numBoard - self.tracker[thisJID]
                                councilNum = (self.numBoard + self.numCouncil) - self.tracker[thisJID]
                                #logging.debug("BOARD NUM IS " + str(boardNum))
                                #logging.debug("BOARD YES VOTES ARE NOW " + str(self.boardcounter[thisJID]))
                                #logging.debug("COUNCIL NUM IS " + str(councilNum))
                                #logging.debug("COUNCIL YES VOTES ARE NOW " + str(self.councilcounter[thisJID]))
                                #logging.debug("AND THE TRACKER IS ... " + str(self.tracker[thisJID]))
                                #thisQuestion = self.questions[self.tracker[thisJID]]
                                thisQuestion = self.questions[self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]]]
                                if (boardNum > 0):
                                    #logging.debug("WE ARE COUNTING BOARD VOTES")
                                    if (inMsg == 'yes'):
                                        ## check to make sure this person hasn't already voted for the maximum number of board candidates
                                        if (self.boardcounter[thisJID] == self.maxBoard):
                                            #print ("hit the max for board")
                                            #self.votecounter[thisJID].append('no')
                                            self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = 'no'
                                            msgText = '\nNote: You have already voted for ' + str(self.maxBoard) + ' Board candidates. Further yes votes will not be counted!!! If this is a problem, please contact gnauck@jabber.org\n\n*****************\nBoard Candidate #' + str(self.tracker[thisJID] + 1) + '... ' + thisQuestion + '\n*****************\nPlease type yes or no depending on how you want to vote for this person.'
                                        else:
                                            #self.votecounter[thisJID].append(inMsg)
                                            self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = inMsg
                                            self.boardcounter[thisJID] = self.boardcounter[thisJID] + 1
                                            self.boardLeft = self.maxBoard - self.boardcounter[thisJID]
                                            #logging.debug("BOARD YES VOTES ARE NOW " + str(self.boardcounter[thisJID]))
                                            msgText = 'Note: You have already voted for ' + str(self.boardcounter[thisJID]) + ' Board candidate(s), you may vote for ' + str(self.boardLeft) + ' more!\n\n*****************\nBoard Candidate #' + str(self.tracker[thisJID] + 1) + '... ' + thisQuestion + '\n*****************'
                                    else:
                                        #self.votecounter[thisJID].append(inMsg)
                                        self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = inMsg
                                        msgText = '\n*****************\nBoard Candidate #' + str(self.tracker[thisJID] + 1) + '... ' + thisQuestion + '\n*****************'
                                elif (boardNum == 0):
                                    #logging.debug("WE ARE STILL COUNTING BOARD VOTES")
                                    if (inMsg == 'yes'):
                                        ## check to make sure this person hasn't already voted for the maximum number of board candidates
                                        if (self.boardcounter[thisJID] == self.maxBoard):
                                            #print ("hit the max for board")
                                            #self.votecounter[thisJID].append('no')
                                            self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = 'no'
                                            msgText = '\nNote: You have already voted for ' + str(self.maxBoard) + ' Board candidates. Your last yes vote will be recorded as a no!!! If this is a problem, contact gnauck@jabber.org for assistance.\n\nThank you for voting on the Board members. We will now move on to voting for the Council.\n\n*****************\nCouncil Candidate #' + str(self.tracker[thisJID] - self.numBoard + 1) + '... ' + thisQuestion + '\n*****************\nPlease type yes or no depending on how you want to vote for this person.'
                                        else:
                                            #self.votecounter[thisJID].append(inMsg)
                                            self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = inMsg
                                            self.boardcounter[thisJID] = self.boardcounter[thisJID] + 1
                                            msgText = '\nThank you for voting on the Board members. We will now move on to voting for the Council.\n\n*****************\nCouncil Candidate #' + str(self.tracker[thisJID] - self.numBoard + 1) + '... ' + thisQuestion + '\n*****************\nPlease type yes or no depending on how you want to vote for this person.'
                                    else:
                                        # self.votecounter[thisJID].append(inMsg)
                                        self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = inMsg
                                        msgText = '\nThank you for voting on the Board members. We will now move on to voting for the Council.\n\n*****************\nCouncil Candidate #' + str(self.tracker[thisJID] - self.numBoard + 1) + '... ' + thisQuestion + '\n*****************\nPlease type yes or no depending on how you want to vote for this person.'
                                elif (councilNum > 0):
                                    if (inMsg == 'yes'):
                                        ## check to make sure this person hasn't already voted for the maximum number of council candidates
                                        #logging.debug("COUNCIL YES VOTES ARE NOW " + str(self.councilcounter[thisJID]))
                                        #logging.debug("MAX COUNCIL IS " + str(self.maxCouncil))
                                        if (self.councilcounter[thisJID] == self.maxCouncil):
                                            #print ("hit the max for council!!!")
                                            #self.votecounter[thisJID].append('no')
                                            self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = 'no'
                                            msgText = '\nNote: You have already voted for ' + str(self.maxCouncil) + ' Council candidates. Further yes votes will not be counted!!! If this is a problem, please contact gnauck@jabber.org for assistance.\n'
                                            #logging.debug("HEY, THE COUNCIL NUM IS " + str(councilNum))
                                            if (councilNum == 0):
                                                msgText = msgText + '\n*****************\nOther matters subject to a vote...\n' + thisQuestion + '\n*****************'
                                            else:
                                                self.councilLeft = self.maxCouncil - self.councilcounter[thisJID]
                                                msgText = 'Note: You have already voted for ' + str(self.councilcounter[thisJID]) + ' Council candidate(s), you may vote for ' + str(self.councilLeft) + ' more!\n\n*****************\nCouncil Candidate #' + str(self.tracker[thisJID] - self.numBoard + 1) + '... ' + thisQuestion + '\n*****************\nPlease type yes or no depending on how you want to vote for this person.'
                                        else:
                                            #self.votecounter[thisJID].append(inMsg)
                                            self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = inMsg
                                            #logging.debug("ABOUT TO COUNT A COUNCIL YES VOTE, THEY ARE CURRENTLY " + str(self.councilcounter[thisJID]))
                                            self.councilcounter[thisJID] = self.councilcounter[thisJID] + 1
                                            #logging.debug("COUNCIL YES VOTES ARE NOW " + str(self.councilcounter[thisJID]))
                                            self.councilLeft = self.maxCouncil - self.councilcounter[thisJID]
                                            msgText = 'Note: You have already voted for ' + str(self.councilcounter[thisJID]) + ' Council candidate(s), you may vote for ' + str(self.councilLeft) + ' more!\n\n*****************\nCouncil Candidate #' + str(self.tracker[thisJID] - self.numBoard + 1) + '... ' + thisQuestion + '\n*****************\nPlease type yes or no depending on how you want to vote for this person.'
                                            if (self.councilcounter[thisJID] == self.maxCouncil):
                                                #print ("hit the max for council!!!!")
                                                msgText = msgText + '\n*****************\nNote: You have already voted for ' + str(self.maxCouncil) + ' Council candidates. Further yes votes will not be counted!!! If this is a problem, please contact gnauck@jabber.org\n*****************'
                                    else:
                                        #self.votecounter[thisJID].append(inMsg)
                                        self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = inMsg
                                        self.councilLeft = self.maxCouncil - self.councilcounter[thisJID]
                                        msgText = 'Note: You have already voted for ' + str(self.councilcounter[thisJID]) + ' Council candidate(s), you may vote for ' + str(self.councilLeft) + ' more!\n\n*****************\nCouncil Candidate #' + str(self.tracker[thisJID] - self.numBoard + 1) + '... ' + thisQuestion + '\n*****************\nPlease type yes or no depending on how you want to vote for this person.'
                                else:
                                    #logging.debug("OTHER BUSINESS...")
                                    self.votecounter[thisJID].append(inMsg)
                                    self.businesscounter[thisJID] = self.businesscounter[thisJID] + 1
                                    msgText = '\n*****************\nOther Business...\n' + thisQuestion + '\n*****************\nPlease type yes or no depending on how you want to vote on this item.'
                            ##### YES/NO SURVEYS
                            elif (self.surveyType == 'yesno'):
                                #self.votecounter[thisJID].append(inMsg)
                                self.votecounter[thisJID][self.surveyOrder[thisJID][self.tracker[thisJID]-1]] = inMsg
                                thisQuestion = self.questions[self.surveyOrder[thisJID][self.tracker[thisJID]]]
                                msgText = '\n*****************\nQuestion #' + str(self.tracker[thisJID] + 1) + '... ' + thisQuestion + '\n*****************\nPlease type yes or no depending on how you want to vote on this question.'
                            else:
                                self.votecounter[thisJID].append(inMsg)
                                thisQuestion = self.questions[self.tracker[thisJID]]
                                msgText = '\n*****************\nApplicant #' + str(self.tracker[thisJID] + 1) + '... ' + thisQuestion + '\n*****************\nPlease type yes or no depending on how you want to vote for this person.'
                            #logging.debug("THE NUMBER OF ITEMS IS " + str(self.numberOfItems))
                            self.tracker[thisJID] = self.tracker[thisJID] + 1
                            #logging.debug("VOTE RECORDED, THE TRACKER IS NOW " + str(self.tracker[thisJID]))
                        else:
                            ## incorrect vote
                            msgText = 'You must vote yes or no. Please try again.'
                    elif (self.tracker[thisJID] == self.numberOfItems):
                        #logging.debug("handling last vote")
                        #logging.debug('message is: ' + inMsg)
                        if ((inMsg == 'yes') or (inMsg == 'no')):
                            ## count the vote
                            #logging.debug("counting last vote!")
                            if (self.surveyType == 'boardcouncil'):
                                boardNum = self.numBoard - self.tracker[thisJID]
                                councilNum = (self.numBoard + self.numCouncil) - self.tracker[thisJID]
                                #logging.debug("BOARD NUM IS " + str(boardNum))
                                #logging.debug("BOARD YES VOTES ARE CURRENTLY " + str(self.boardcounter[thisJID]))
                                #logging.debug("COUNCIL NUM IS " + str(councilNum))
                                #logging.debug("COUNCIL YES VOTES ARE CURRENTLY " + str(self.councilcounter[thisJID]))
                                #logging.debug("NUM BUSINESS IS  " + str(self.numBusiness))
                                #logging.debug("NUM TOTAL IS  " + str(self.numberOfItems))
                                if (inMsg == 'yes'):
                                    ## check to make sure this person hasn't already voted for the maximum number of candidates
                                    if (self.numBusiness > 0):
                                        self.votecounter[thisJID].append(inMsg)
                                        msgText = '\n*****************\nThank you for completing the survey! If you have any questions or would like to change your votes, please contact gnauck@jabber.org'
                                    elif (self.councilcounter[thisJID] == self.maxCouncil):
                                        #print ("hit the max for council")
                                        #self.votecounter[thisJID].append('no')
                                        self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = 'no'
                                        msgText = '\nNote: You have already voted for ' + str(self.maxCouncil) + ' Council candidates. Your final yes vote will be recorded as a no!!! If this is a problem, contact gnauck@jabber.org for assistance.\n\n*****************\nThank you for completing the survey! If you have any questions or would like to change your votes, please contact gnauck@jabber.org'
                                    else:
                                        #self.votecounter[thisJID].append(inMsg)
                                        self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = inMsg
                                        msgText = '\n*****************\nThank you for completing the survey! If you have any questions or would like to change your votes, please contact gnauck@jabber.org'
                                else:
                                    #self.votecounter[thisJID].append(inMsg)
                                    self.votecounter[thisJID][self.boardCouncilQuestionsOrder[thisJID][self.tracker[thisJID]-1]] = inMsg
                                    msgText = '\n*****************\nThank you for completing the survey! If you have any questions or would like to change your votes, please contact gnauck@jabber.org'
                            else:
                                self.votecounter[thisJID][self.surveyOrder[thisJID][self.tracker[thisJID]-1]] = inMsg
                                msgText = '\n*****************\nThank you for completing the survey! If you have any questions or would like to change your votes, please contact gnauck@jabber.org'
                            self.tracker[thisJID] = self.tracker[thisJID] + 1
                            #logging.debug("SURVEY COMPLETED, THE TRACKER IS NOW " + str(self.tracker[thisJID]))
                            ## record complete survey results for this user...
                            #logging.debug("recording voting results for " + str(thisJID))
                            ## create respondent DOM
                            answerDoc = Document()
                            ## create root node of <respondent>
                            answerDocRoot = answerDoc.createElement("respondent")
                            ## set 'jid' attribute equal to thisJID
                            answerDocJID = answerDocRoot.setAttribute("jid", thisJID)
                            answerDoc.appendChild(answerDocRoot)
                            #logging.debug(answerDoc.childNodes[0])
                            #logging.debug(answerDoc.childNodes[0].getAttribute("jid"))
                            ## create <questions> child
                            vc = 0
                            if self.surveyType == "yesno":
                                #logging.debug("recording votes for simple yes or no questions")
                                for vc, x in enumerate(self.votecounter[thisJID]):
                                    ## create <answer> child 
                                    thisAnswerDocElement = "answer" + str(self.questArray[vc])
                                    thisAnswer = answerDoc.createElement(thisAnswerDocElement)
                                    answerDocRoot.appendChild(thisAnswer)
                                    ## create text value equal to x
                                    answerText = answerDoc.createTextNode(x)
                                    thisAnswer.appendChild(answerText)
                            elif self.surveyType == "acceptmembers":
                                #logging.debug("recording votes for accepting new JSF members")
                                for x in self.votecounter[thisJID]:
                                    ## create <answer> child 
                                    thisAnswer = answerDoc.createElement("answer")
                                    ## set 'name' attribute for this applicant
                                    thisApp = self.appNames[vc]
                                    answerApplicant = thisAnswer.setAttribute("name", thisApp)
                                    answerDocRoot.appendChild(thisAnswer)
                                    ## create text value equal to x
                                    answerText = answerDoc.createTextNode(x)
                                    thisAnswer.appendChild(answerText)
                                    vc = vc + 1
                            elif self.surveyType == "boardcouncil":
                                #logging.debug("recording votes for Board and Council")
                                bc = 0
                                cc = 0
                                tbc = 0
                                tcc = 0
                                mc = 0
                                tmc = 0
                                ## create <board> child 
                                boardAnswerNode = answerDoc.createElement("board")
                                for x in self.votecounter[thisJID]:
                                    candNode = (self.mainQuestNode.getElementsByTagName("item")[tbc])
                                    candFirst = (candNode.getElementsByTagName("first_name")[0])
                                    firstText = self._getText(candFirst.childNodes)
                                    candLast = (candNode.getElementsByTagName("last_name")[0])
                                    lastText = self._getText(candLast.childNodes)
                                    nameText = firstText + ' ' + lastText
                                    candText = candNode.attributes["type"]
                                    candType = candText.value
                                    logging.debug("CANDIDATE NAME IS " + nameText)
                                    logging.debug("CANDIDATE TYPE IS " + str(candType))
                                    if (candType == 'board'):
                                        ## create <item> child 
                                        thisAnswer = answerDoc.createElement("item")
                                        ## set 'name' attribute for this applicant
                                        thisDude = self.boardArray[bc]
                                        answerName = thisAnswer.setAttribute("name", thisDude)
                                        boardAnswerNode.appendChild(thisAnswer)
                                        ## create text value equal to x
                                        boardText = answerDoc.createTextNode(x)
                                        thisAnswer.appendChild(boardText)
                                        answerDocRoot.appendChild(boardAnswerNode)
                                        logging.debug(answerDoc.childNodes[0])
                                        bc = bc + 1
                                    else:
                                        pass
                                    tbc = tbc + 1
                                ## create <council> child 
                                councilAnswerNode = answerDoc.createElement("council")
                                for x in self.votecounter[thisJID]:
                                    candNode = (self.mainQuestNode.getElementsByTagName("item")[tcc])
                                    candFirst = (candNode.getElementsByTagName("first_name")[0])
                                    firstText = self._getText(candFirst.childNodes)
                                    candLast = (candNode.getElementsByTagName("last_name")[0])
                                    lastText = self._getText(candLast.childNodes)
                                    nameText = firstText + ' ' + lastText
                                    candText = candNode.attributes["type"]
                                    candType = candText.value
                                    #logging.debug("CANDIDATE NAME IS " + nameText)
                                    #logging.debug("CANDIDATE TYPE IS " + str(candType))
                                    if (candType == 'council'):
                                        ## create <item> child 
                                        thisAnswer = answerDoc.createElement("item")
                                        ## set 'name' attribute for this applicant
                                        thisDude = self.councilArray[cc]
                                        answerName = thisAnswer.setAttribute("name", thisDude)
                                        councilAnswerNode.appendChild(thisAnswer)
                                        ## create text value equal to x
                                        councilText = answerDoc.createTextNode(x)
                                        thisAnswer.appendChild(councilText)
                                        answerDocRoot.appendChild(councilAnswerNode)
                                        #logging.debug(answerDoc.childNodes[0])
                                        cc = cc + 1
                                    else:
                                        pass
                                    tcc = tcc + 1
                                #logging.debug(answerDoc.childNodes[0])
                                ## create <business> child (but only if necessary)
                                businessAnswerNode = answerDoc.createElement("business")
                                for x in self.votecounter[thisJID]:
                                    candNode = (self.mainQuestNode.getElementsByTagName("item")[tmc])
                                    candFirst = (candNode.getElementsByTagName("first_name")[0])
                                    firstText = self._getText(candFirst.childNodes)
                                    candLast = (candNode.getElementsByTagName("last_name")[0])
                                    lastText = self._getText(candLast.childNodes)
                                    nameText = firstText + ' ' + lastText
                                    candText = candNode.attributes["type"]
                                    candType = candText.value
                                    #logging.debug("ITEM NAME IS " + nameText)
                                    #logging.debug("ITEM TYPE IS " + str(candType))
                                    if (candType == 'otherbusiness'):
                                        ## create <item> child 
                                        thisAnswer = answerDoc.createElement("item")
                                        ## set 'name' attribute for this item
                                        thisDude = self.businessArray[mc]
                                        answerName = thisAnswer.setAttribute("name", thisDude)
                                        businessAnswerNode.appendChild(thisAnswer)
                                        ## create text value equal to x
                                        businessText = answerDoc.createTextNode(x)
                                        thisAnswer.appendChild(businessText)
                                        answerDocRoot.appendChild(businessAnswerNode)
                                        #logging.debug(answerDoc.childNodes[0])
                                        mc = mc + 1
                                    else:
                                        pass
                                    tmc = tmc + 1
                                #logging.debug(answerDoc.childNodes[0])
                            ## write to document jid.xml in surveydir/ directory
                            fileName = self.surveyDir + thisJID + '.xml'
                            #logging.debug('WRITING TO FILE ' + fileName)

                            import codecs
                            newFile = codecs.open(fileName, "w", "utf-8")
                            docString = answerDoc.toxml()
                            newFile.write(docString)
                            newFile.close()
                            msgText = 'Thank you for completing the survey! If you have any questions or would like to change your votes, please contact gnauck@jabber.org'
                        else:
                            ## incorrect vote
                            #logging.debug("last vote is incorrect!")
                            msgText = 'You must vote yes or no. Please try again.'
                    else:
                        msgText = 'something went horribly wrong!'
                msgType = 'chat'
                #print "<%s> %s" % (JID, msg.getBody())
            ## we don't talk with people who aren't in the roster
            else:
                msgText = 'Sorry, I don\'t talk with strangers. If you think you belong in my roster but have not yet been added, please contact gnauck@jabber.org'
                msgType = 'chat'
            self.bot.sendMessage(msg['jid'], msgText, mtype=msgType)
            #self._send_test_form(thisJID)

    def _handleSurvey(self):
        qc = 0
        if self.surveyType == "yesno":
            for question in self.mainQuestNode.getElementsByTagName("question"):
                ## construct survey text for this question
                questsNode = (self.mainQuestNode.getElementsByTagName("question")[qc])
                textNode = (questsNode.getElementsByTagName("text")[0])
                questText = self._getText(textNode.childNodes)
                questText = '\n' + questText + '\n'
                self.questArray[qc] = qc
                self.questions.append(questText)
                qc = qc + 1
        elif self.surveyType == "acceptmembers":
            for applicant in self.mainQuestNode.getElementsByTagName("applicant"):
                ## construct survey text for this applicant
                appsNode = (self.mainQuestNode.getElementsByTagName("applicant")[qc])
                appFirst = (appsNode.getElementsByTagName("first_name")[0])
                firstText = self._getText(appFirst.childNodes)
                appLast = (appsNode.getElementsByTagName("last_name")[0])
                lastText = self._getText(appLast.childNodes)
                nameText = firstText + ' ' + lastText
                #logging.debug("name is " + nameText)
                self.appNames[qc] = nameText
                nameText = 'Name: ' + nameText
                appJID = (appsNode.getElementsByTagName("jid")[0])
                jidText = 'JID: ' + self._getText(appJID.childNodes)
                googleURL = 'http://www.google.com/search?as_q=' + firstText + '+' + lastText + '&num=50&hl=en&ie=UTF-8&oe=UTF-8&btnG=Google+Search&as_epq=&as_oq=&as_eq=&lr=&as_ft=i&as_filetype=&as_qdr=all&as_occt=any&as_dt=i&as_sitesearch=mailman.jabber.org&safe=images'
                googleText = 'Google result for mailing list activity (click to see how active this person is on the mailing lists!): ' + '\n' + googleURL
                appNotes = (appsNode.getElementsByTagName("notes")[0])
                noteText = 'Application: ' + self._getText(appNotes.childNodes)
                appText = '\n\n' + nameText + '\n\n' + jidText + '\n\n' + googleText + '\n\n' + noteText
                self.questions.append(appText)
                qc = qc + 1
        elif self.surveyType == "boardcouncil":
            bc = 0
            cc = 0
            mc = 0
            for item in self.mainQuestNode.getElementsByTagName("item"):
                ## construct survey text for this candidate
                candNode = (self.mainQuestNode.getElementsByTagName("item")[qc])
                candFirst = (candNode.getElementsByTagName("first_name")[0])
                firstText = self._getText(candFirst.childNodes)
                candLast = (candNode.getElementsByTagName("last_name")[0])
                lastText = self._getText(candLast.childNodes)
                nameText = firstText + ' ' + lastText
                typeText = candNode.attributes["type"]
                candType = typeText.value
                if (candType == 'board'):
                    self.boardArray[bc] = nameText
                    #logging.debug("board candidate # " + str(bc) + " is " + str(self.boardArray[bc]))
                    bc = bc + 1
                elif (candType == 'council'):
                    self.councilArray[cc] = nameText
                    #logging.debug("council candidate # " + str(cc) + " is " + str(self.councilArray[cc]))
                    cc = cc + 1
                elif (candType == 'otherbusiness'):
                    self.businessArray[mc] = nameText
                    #logging.debug("other # " + str(mc) + " is " + str(self.businessArray[mc]))
                    mc = mc + 1
                candURL = (candNode.getElementsByTagName("text")[0])
                urlText = 'Details: ' + self._getText(candURL.childNodes)
                appText = '\n' + nameText + '\n' + '\n' + urlText
                self.questions.append(appText)
                #logging.debug("### THE QUESTION COUNT IS ... " + str(qc))
                #logging.debug("### THIS QUESTION IS ... " + self.questions[qc])
                qc = qc + 1
                
    def _set_responses(self):
        self.responses = { 'yesno_initial_response' : 'Great! There are %(numQuest)d questions to answer. I will present each question to you and expect you to type yes or no. \n\nPlease type ok to begin.',
                           'accepetmembers_initial_response' : 'Great! PLEASE READ THE FOLLOWING INSTRUCTIONS.\n\nThere are %(numApp)d applicants to vote on. I will present each applicant to you and expect you to type yes or no.\n\nNOTE: By proceeding further, you affirm that you wish your vote to count as a proxy vote in the official electronic meeting to be held on April 23, 2003. \n\nTo begin proxy voting, please type ok.',
                           'boardcouncil_initial_response_2parts' : '\n\nGreat! This election has two parts: (1) votes for the Board and (2) votes for the Council. There are %(numBoard)d candidates for the Board, of which you may vote for up to %(maxBoard)d. There are %(numCouncil)d candidates for the Council, of which you may vote for up to %(maxCouncil)d. I will present each applicant to you and expect you to type yes or no.\n\nNOTE: By proceeding further, you affirm that you wish your vote to count as a proxy vote in the official electronic meeting to be held on %(meetingDate)s . \n\nTo begin proxy voting, please type ok.',
                           'boardcouncil_initial_response_3parts' : '\n\nGreat! This election has several parts: (1) votes for the Board, (2) votes for the Council, and (3) other matters subject to a vote. There are %(numBoard)d candidates for the Board, of which you may vote for up to %(maxBoard)d. There are %(numCouncil)d candidates for the Council, of which you may vote for up to %(maxCouncil)d. There are %(numBusiness)d other matters to vote on. I will present each Board and Council applicant to you and expect you to type yes or no -- please read the full list of candidates at http://wiki.jabber.org/index.php/Board_and_Council_Elections before you start voting. Then I will present the other matters to vote on.\n\nNOTE: By proceeding further, you affirm that you wish your vote to count as a proxy vote in the official electronic meeting to be held on %(meetingDate)s . \n\nTo begin proxy voting, please type ok.',
                           'default_msg' : 'This is default message - this means something went WRONG. You should get more verbose text instead of this one.',
                           'already_completed_msg' : 'Sorry, you have already completed this survey. If you have any questions, please contact gnauck@jabber.org',
                           'boardcouncil_vote_msg' : '\n*****************\nBoard Candidate #%(candidateNum)d... %(question)s\n*****************\nPlease type yes or no depending on how you want to vote for this person.',
                           'yesno_vote_msg' : '\n*****************\nQuestion #%(questionNum)d... %(question)s\n*****************\nPlease type yes or no depending on how you want to vote on this question.',
                           'application_vote_msg' : '\n*****************\nApplicant #%(applicantNum)d... %(question)s\n*****************\nPlease type yes or no depending on how you want to vote for this person.',
                           'ok_bye_msg' : 'OK, bye!',
                           'would_vote_msg' : 'Would you like to vote on the current topic? Please answer yes or no.'
            
        }
