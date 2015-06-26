import os
import unittest
import time
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *


#------------------------------------------------------------
#
# Locator
#
class Locator(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Locator" # TODO make this more human readable by adding spaces
    self.parent.categories = ["IGT"]
    self.parent.dependencies = []
    self.parent.contributors = ["Junichi Tokuda, Wei Wang, Ehud Schmidt (BWH)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    A communication interface for Koh Young's 3D sensors.
    """
    self.parent.acknowledgementText = """
    This work is supported by NIH National Center for Image Guided Therapy (P41EB015898).
    """ 
    # replace with organization, grant and thanks.


#------------------------------------------------------------
#
# LocatorWidget
#
class LocatorWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Instantiate and connect widgets ...

    self.logic = LocatorLogic(None)
    self.logic.setWidget(self)
    self.nLocators = 5

    #--------------------------------------------------
    # For debugging
    #
    # Reload and Test area
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    self.layout.addWidget(reloadCollapsibleButton)
    reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    reloadCollapsibleButton.collapsed = True
    
    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "CurveMaker Reload"
    reloadFormLayout.addWidget(self.reloadButton)
    self.reloadButton.connect('clicked()', self.onReload)
    #
    #--------------------------------------------------


    #--------------------------------------------------
    # GUI components
    
    #
    # Registration Matrix Selection Area
    #
    selectionCollapsibleButton = ctk.ctkCollapsibleButton()
    selectionCollapsibleButton.text = "Locator ON/OFF"
    self.layout.addWidget(selectionCollapsibleButton)
  
    selectionFormLayout = qt.QFormLayout(selectionCollapsibleButton)
    
    self.transformSelector = []
    self.locatorActiveCheckBox = []

    for i in range(self.nLocators):

      self.transformSelector.append(slicer.qMRMLNodeComboBox())
      selector = self.transformSelector[i]
      selector.nodeTypes = ( ("vtkMRMLLinearTransformNode"), "" )
      selector.selectNodeUponCreation = True
      selector.addEnabled = False
      selector.removeEnabled = False
      selector.noneEnabled = False
      selector.showHidden = False
      selector.showChildNodeTypes = False
      selector.setMRMLScene( slicer.mrmlScene )
      selector.setToolTip( "Establish a connection with the server" )

      self.locatorActiveCheckBox.append(qt.QCheckBox())
      checkbox = self.locatorActiveCheckBox[i]
      checkbox.checked = 0
      checkbox.text = ' '
      checkbox.setToolTip("Activate locator")

      transformLayout = qt.QHBoxLayout()
      transformLayout.addWidget(selector)
      transformLayout.addWidget(checkbox)
      selectionFormLayout.addRow("Locator #%d:" % i, transformLayout)

      checkbox.connect('toggled(bool)', self.onLocatorActive)

    #--------------------------------------------------
    # connections
    #

    # Add vertical spacer
    self.layout.addStretch(1)


  def cleanup(self):
    pass


  def onLocatorActive(self):

    removeList = {}
    for i in range(self.nLocators):
      tnode = self.transformSelector[i].currentNode()
      if self.locatorActiveCheckBox[i].checked == True:
        if tnode:
          self.transformSelector[i].setEnabled(False)
          self.logic.addLocator(tnode)
          mnodeID = tnode.GetAttribute('Locator')
          removeList[mnodeID] = False
        else:
          self.locatorActiveCheckBox[i].setChecked(False)
          self.transformSelector[i].setEnabled(True)
      else:
        if tnode:
          mnodeID = tnode.GetAttribute('Locator')
          if mnodeID != None and not (mnodeID in removeList):
            removeList[mnodeID] = True
            self.logic.unlinkLocator(tnode)
        self.transformSelector[i].setEnabled(True)

    for k, v in removeList.iteritems():
      if v:
        pass
        #self.logic.removeLocator(k)
      

  def onReload(self, moduleName="Locator"):
    # Generic reload method for any scripted module.
    # ModuleWizard will subsitute correct default moduleName.

    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)


  def updateGUI(self):
    # Enable/disable GUI components based on the state machine

    ##if self.logic.connected():
    #if self.logic.active():
    #  self.activeCheckBox.setChecked(True)
    #else:
    #  self.activeCheckBox.setChecked(False)
    #
    ## Enable/disable 'Active' checkbox 
    #if self.connectorSelector.currentNode():
    #  self.activeCheckBox.setEnabled(True)
    #else:
    #  self.activeCheckBox.setEnabled(False)
    pass



#------------------------------------------------------------
#
# LocatorLogic
#
class LocatorLogic(ScriptedLoadableModuleLogic):

  def __init__(self, parent):
    ScriptedLoadableModuleLogic.__init__(self, parent)

    self.scene = slicer.mrmlScene
    self.scene.AddObserver(slicer.vtkMRMLScene.NodeRemovedEvent, self.onNodeRemovedEvent)
    self.widget = None

    self.eventTag = {}

    # IGTL Conenctor Node ID
    self.connectorNodeID = ''

    self.count = 0
    
  def setWidget(self, widget):
    self.widget = widget


  def addLocator(self, tnode):
    if tnode:
      if tnode.GetAttribute('Locator') == None:
        needleModelID = self.createNeedleModelNode("Needle_%s" % tnode.GetName())
        needleModel = self.scene.GetNodeByID(needleModelID)
        needleModel.SetAndObserveTransformNodeID(tnode.GetID())
        tnode.SetAttribute('Locator', needleModelID)

  def unlinkLocator(self, tnode):
    if tnode:
      print 'unlinkLocator(%s)' % tnode.GetID()
      tnode.RemoveAttribute('Locator')

  def removeLocator(self, mnodeID):
    if mnodeID:
      print 'removeLocator(%s)' % mnodeID
      mnode = self.scene.GetNodeByID(mnodeID)
      if mnode:
        print 'removing from the scene'
        dnodeID = mnode.GetDisplayNodeID()
        if dnodeID:
          dnode = self.scene.GetNodeByID(dnodeID)
          if dnode:
            self.scene.RemoveNode(dnode)
        self.scene.RemoveNode(mnode)

  def onNewDeviceEvent(self, caller, event, obj=None):

    cnode = self.scene.GetNodeByID(self.connectorNodeID)
    nInNode = cnode.GetNumberOfIncomingMRMLNodes()
    print nInNode
    for i in range (nInNode):
      node = cnode.GetIncomingMRMLNode(i)
      if not node.GetID() in self.eventTag:
        self.eventTag[node.GetID()] = node.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onIncomingNodeModifiedEvent)
        if node.GetNodeTagName() == 'IGTLTrackingDataSplitter':
          n = node.GetNumberOfTransformNodes()
          for id in range (n):
            tnode = node.GetTransformNode(id)
            if tnode and tnode.GetAttribute('Locator') == None:
              print "No Locator"
              needleModelID = self.createNeedleModelNode("Needle_%s" % tnode.GetName())
              needleModel = self.scene.GetNodeByID(needleModelID)
              needleModel.SetAndObserveTransformNodeID(tnode.GetID())
              needleModel.InvokeEvent(slicer.vtkMRMLTransformableNode.TransformModifiedEvent)
              tnode.SetAttribute('Locator', needleModelID)

  def createNeedleModel(self, node):
    if node and node.GetClassName() == 'vtkMRMLIGTLTrackingDataBundleNode':
      n = node.GetNumberOfTransformNodes()
      print n
      for id in range (n):
        tnode = node.GetTransformNode(id)
        if tnode:
          needleModelID = self.createNeedleModelNode("Needle_%s" % tnode.GetName())
          needleModel = self.scene.GetNodeByID(needleModelID)
          needleModel.SetAndObserveTransformNodeID(tnode.GetID())
          needleModel.InvokeEvent(slicer.vtkMRMLTransformableNode.TransformModifiedEvent)

        
  def createNeedleModelNode(self, name):

    locatorModel = self.scene.CreateNodeByClass('vtkMRMLModelNode')
    
    # Cylinder represents the locator stick
    cylinder = vtk.vtkCylinderSource()
    cylinder.SetRadius(1.5)
    cylinder.SetHeight(100)
    cylinder.SetCenter(0, 0, 0)
    cylinder.Update()

    # Rotate cylinder
    tfilter = vtk.vtkTransformPolyDataFilter()
    trans =   vtk.vtkTransform()
    trans.RotateX(90.0)
    trans.Translate(0.0, -50.0, 0.0)
    trans.Update()
    if vtk.VTK_MAJOR_VERSION <= 5:
      tfilter.SetInput(cylinder.GetOutput())
    else:
      tfilter.SetInputConnection(cylinder.GetOutputPort())
    tfilter.SetTransform(trans)
    tfilter.Update()

    # Sphere represents the locator tip
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(3.0)
    sphere.SetCenter(0, 0, 0)
    sphere.Update()

    apd = vtk.vtkAppendPolyData()

    if vtk.VTK_MAJOR_VERSION <= 5:
      apd.AddInput(sphere.GetOutput())
      apd.AddInput(tfilter.GetOutput())
    else:
      apd.AddInputConnection(sphere.GetOutputPort())
      apd.AddInputConnection(tfilter.GetOutputPort())
    apd.Update()
    
    locatorModel.SetAndObservePolyData(apd.GetOutput());

    self.scene.AddNode(locatorModel)
    locatorModel.SetScene(self.scene);
    locatorModel.SetName(name)
    
    locatorDisp = locatorModel.GetDisplayNodeID()
    if locatorDisp == None:
      locatorDisp = self.scene.CreateNodeByClass('vtkMRMLModelDisplayNode')
      self.scene.AddNode(locatorDisp)
      locatorDisp.SetScene(self.scene)
      locatorModel.SetAndObserveDisplayNodeID(locatorDisp.GetID());
      
    color = [0, 0, 0]
    color[0] = 0.5
    color[1] = 0.5
    color[2] = 1.0
    locatorDisp.SetColor(color)
    
    return locatorModel.GetID()


  def onNodeRemovedEvent(self, caller, event, obj=None):
    delkey = ''
    if obj == None:
      for k in self.eventTag:
        node = self.scene.GetNodeByID(k)
        if node == None:
          delkey = k
          break

    if delkey != '':
      del self.eventTag[delkey]


