from PyQt4 import QtGui, QtCore
from qgis.gui import *
from qgis.core import *
from geoserverexplorer.geoserver import pem

class DefineCatalogDialog(QtGui.QDialog):

    def __init__(self, catalogs, parent = None):
        super(DefineCatalogDialog, self).__init__(parent)
        self.catalogs = catalogs
        self.ok = False
        self.initGui()


    def initGui(self):
        self.setWindowTitle('Catalog definition')

        verticalLayout = QtGui.QVBoxLayout()

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        nameLabel = QtGui.QLabel('Catalog name')
        nameLabel.setMinimumWidth(150)
        self.nameBox = QtGui.QLineEdit()
        settings = QtCore.QSettings()
        name = settings.value('/GeoServer/LastCatalogName', 'Default GeoServer catalog')
        self.nameBox.setText(name)

        self.nameBox.setMinimumWidth(250)
        horizontalLayout.addWidget(nameLabel)
        horizontalLayout.addWidget(self.nameBox)
        verticalLayout.addLayout(horizontalLayout)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        urlLabel = QtGui.QLabel('URL')
        urlLabel.setMinimumWidth(150)
        self.urlBox = QtGui.QLineEdit()
        url = settings.value('/GeoServer/LastCatalogUrl', 'http://localhost:8080/geoserver')
        self.urlBox.setText(url)
        self.urlBox.setMinimumWidth(250)
        horizontalLayout.addWidget(urlLabel)
        horizontalLayout.addWidget(self.urlBox)
        verticalLayout.addLayout(horizontalLayout)

        self.groupBox = QtGui.QGroupBox()
        self.groupBox.setTitle("GeoServer Connection parameters")
        self.groupBox.setLayout(verticalLayout)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.groupBox)
        self.spacer = QtGui.QSpacerItem(20,20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        layout.addItem(self.spacer)

        self.tabWidget = QtGui.QTabWidget()

        tabBasicAuth = QtGui.QWidget()
        tabBasicAuthLayout = QtGui.QVBoxLayout(tabBasicAuth)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        usernameLabel = QtGui.QLabel('User name')
        usernameLabel.setMinimumWidth(150)
        self.usernameBox = QtGui.QLineEdit()
        self.usernameBox.setText('admin')
        self.usernameBox.setMinimumWidth(250)
        horizontalLayout.addWidget(usernameLabel)
        horizontalLayout.addWidget(self.usernameBox)
        tabBasicAuthLayout.addLayout(horizontalLayout)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        passwordLabel = QtGui.QLabel('Password')
        passwordLabel.setMinimumWidth(150)
        self.passwordBox = QtGui.QLineEdit()
        self.passwordBox.setEchoMode(QtGui.QLineEdit.Password)
        self.passwordBox.setText('geoserver')
        self.passwordBox.setMinimumWidth(250)
        horizontalLayout.addWidget(passwordLabel)
        horizontalLayout.addWidget(self.passwordBox)
        tabBasicAuthLayout.addLayout(horizontalLayout)

        self.tabWidget.addTab(tabBasicAuth, "Basic")

        try:
            self.certWidget = QgsAuthConfigSelect( keypasssupported = False)
            self.tabWidget.addTab(self.certWidget, "Configurations")
        except NameError:
            #for QGIS without PKI support
            pass

        verticalLayout3 = QtGui.QVBoxLayout()
        verticalLayout3.addWidget(self.tabWidget)

        self.authBox = QtGui.QGroupBox()
        self.authBox.setTitle("Authentication")
        self.authBox.setLayout(verticalLayout3)

        verticalLayout.addWidget(self.authBox)

        self.spacer = QtGui.QSpacerItem(20,20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        layout.addItem(self.spacer)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Close)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

        self.buttonBox.accepted.connect(self.okPressed)
        self.buttonBox.rejected.connect(self.cancelPressed)

        self.resize(400,200)


    def okPressed(self):
        self.url = unicode(self.urlBox.text().strip('/')     + '/rest')
        if not self.url.startswith('http'):
            self.url = 'http://%s' % self.url
        if self.tabWidget.currentIndex() == 0:
            self.username = unicode(self.usernameBox.text())
            self.password = unicode(self.passwordBox.text())
            self.certfile = None
            self.keyfile = None
            self.cafile = None
            self.authid = None
        else:
            self.username = None
            self.password = None
            self.authid = self.certWidget.configId()
            authtype = QgsAuthManager.instance().configProviderType(self.authid);
            if authtype == QgsAuthType.None or authtype == QgsAuthType.Unknown:
                QtGui.QMessageBox.warning(self, "Authentication needed",
                                  "Please specify a valid authentication for connecting to the catalog")
                return
            if authtype == QgsAuthType.Basic:
                configbasic = QgsAuthConfigBasic()
                QgsAuthManager.instance().loadAuthenticationConfig(self.authid, configbasic, True)
                self.password = configbasic.password()
                self.username = configbasic.username()
            elif authtype in [QgsAuthType.PkiPaths, QgsAuthType.PkiPkcs12]:
                self.certfile, self.keyfile, self.cafile = pem.getPemPkiPaths(self.authid, authtype)
            else:
                QtGui.QMessageBox.warning(self, "Unsupported authentication",
                                  "The selected authentication type is not supported")
                return

        self.name = unicode(self.nameBox.text())
        name = self.name
        i = 2
        while name in self.catalogs.keys():
            name = self.name + "_" + str(i)
            i += 1
        self.name = name
        settings = QtCore.QSettings()
        settings.setValue('/GeoServer/LastCatalogName', self.nameBox.text())
        settings.setValue('/GeoServer/LastCatalogUrl', self.urlBox.text())
        saveCatalogs = bool(settings.value("/GeoServer/Settings/GeoServer/SaveCatalogs", True, bool))
        if saveCatalogs:
            settings.beginGroup("/GeoServer/Catalogs/" + self.name)
            settings.setValue("url", self.url);
            if self.authid is not None:
                settings.setValue("authid", self.authid)
            else:
                settings.setValue("username", self.username)
            settings.endGroup()
        self.ok = True
        self.close()

    def cancelPressed(self):
        self.ok = False
        self.close()