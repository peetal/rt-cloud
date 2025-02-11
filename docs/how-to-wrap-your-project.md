# **Making your project cloud enabled**
Make a new directory under rt-cloud/projects for your project.
Use the sample project in *rt-cloud/projects/sample* as a template for making your python script cloud enabled. The sample.py script corresponds to the script you will make for your experiment.

## **Project Code**
You'll need to copy several blocks of code to your project to get it cloud enabled. These are:

### **Initialization code**

Accept at least the following command line parameters in your project python file:

    argParser = argparse.ArgumentParser()
    argParser.add_argument('--config', '-c', default=defaultConfig, type=str,
                           help='experiment config file (.json or .toml)')
    argParser.add_argument('--runs', '-r', default='', type=str,
                           help='Comma separated list of run numbers')
    argParser.add_argument('--scans', '-s', default='', type=str,
                           help='Comma separated list of scan number')
    args = argParser.parse_args()

Create an clientInterface instance for communicating with the projectInterface. The clientInterface automatically connects to a localhost projectInterface when created.

    clientInterface = ClientInterface()

The clientInterface provides several interfaces for retrieving data, giving subject feedback, and updating the user's webpage.

    dataInterface = clientInterfaces.dataInterface
    subjInterface = clientInterfaces.subjInterface
    webInterface  = clientInterfaces.webInterface

Note: The clientInterfaces connect to remote services with the following mapping:

    dataInterface --> scannerDataService
    subjInterface --> subjectService
    webInterface  --> user web browser

### **Retrieving DICOM Images from the Scanner Computer**

Within your python script, use the `dataInterface` object to request remote files. For example, to retrieve DICOM images as they are created, init a watch on the appropriate directory and then watch for them.

    dataInterface.initWatch('/tmp/dicoms', 'samp*.dcm', minFileSize)
    rawData = dataInterface.watchFile('/tmp/samp3.dcm')

Or use the readRetryDicom helper function which will retry several times across timeouts to retrieve the DICOM image data:

    dataInterface.initWatch('/tmp/dicoms', 'samp*.dcm', minFileSize)
    dicomData = readRetryDicomFromDataInterface(dataInterface, 'samp3.dcm', timeout=10)

Or use the streaming interface to receive image data:

    streamId = dataInterface.initScannerStream('/tmp/dicoms', 'samp*.dcm', minFileSize)
    dicomData = dataInterface.getImageData(streamId, int(this_TR), timeout=10)

Set the minFileSize parameter to the minimum size expected for DICOM files. This can be determined by listing the sizes of a set of previously collected DICOM files and selecting slightly less than the smallest as the minimumFileSize. The FileWatcher will not return a file until its minimum size has been reached, this helps ensure that a file is completely written before being made available. However, if this parameter is set too high (higher than the file size) the file will never be returned.

### **Send Classification Results for Subject Feedback**

Send classification results to the presentation computer using the subjectInterface setResult() command:

    subjInterface.setResult(runNum, int(TR_id), float(classification_result))

Or send classification results to a file on the scanner computer (where scannerDataService is running) which can be read in by a script (e.g. using a toolkit like PsychToolbox) for subject feedback.

    dataInterface.putFile(fullpath_filename_to_save, text_to_save)

### **Update the User's Webpage Display**
Send data values to be graphed in the projectInterface web page

    webInterface.plotDataPoint(runNum, int(TR_id), float(classification_result))

### **Read Files from the Console Computer (such as configuration files)**
Read files from the console computer using getFile

    data = dataInterface.getFile(fullpath_filename)

Or read the newest file matching a file pattern such as 'samp*.dcm'

    data = dataInterface.getNewestFile(fullpath_filepattern)


### **Load Project Configurations**
RT-Cloud experiments use a TOML file for configuration settings. You can define your own configuration variables just by adding them to the TOML configuration file. Your configuration variables will automatically appear in the web interface 'settings' tab and you can adjust the values from that page.

Use the loadConfigFile function from your experiment script to load your configurations into a structured object

    import rtCommon.utils as utils
    cfg = utils.loadConfigFile(args.config)

Access configurations within your experiment script using the config structure

    print(cfg.subjectName, cfg.subjectDay)

The following fields must be present in the config toml file for the projectInterface to work:
  - runNum = [1]    # an array with one or more run numbers e.g. [1, 2, 3]
  - scanNum = [11]  # an array with one or more scan numbers e.g.  [11, 13, 15]
  - subjectName = 'subject01'
  - subjectDay = 1

Optional parameters used for plotting:
  - title = 'Project Title'
  - plotTitle = 'Plot Title'
  - plotXLabel = 'Sample #'
  - plotYLabel = 'Value'
  - plotXRangeLow = 0
  - plotXRangeHigh = 20
  - plotYRangeLow = -1
  - plotYRangeHigh = 1

Additionally, create any of your own unique parameters that you may need for your experiment.

### **Timeout Settings**
RT-Cloud uses RPC (Remote Procedure Calls) to send command requests from the researcher's experiment script to the dataInterface, subjectInterface and webInterface. There are two RPC hops to handle a request. The first if using rpyc (a native Python RPC library) to make a call from the script to the projectServer. The second is using a WebSocket RPC implemented in rtCommon/remoteable.py and invoked from rtCommon/projectServerRPC.py to make the call from the projectServer to the remote service (such as DataService). Each hop has an adjustable timeout.

The rpyc timeout can be set when the ClientInterface is created in the experiment script, such as in the sample.py project. Simply include the rpyc_timeout= parameter (e.g. ClientInterface(rpyc_timeout=60)), the default is 60 seconds. Rpyc also has a timed() function which can be used to adjust the timeout of individual rpc calls.

The websocket timeout can be set in 1 of 2 ways. Method 1 is to set a larger timeout for all calls using the setRPCTimeout() of remoteable objects. For example to increase the timeout of the dataInterface in the experiment script, call dataInterface.setRPCTimeout(5). The default websocket timeout is 5 seconds. Method 2 is to set a larger timeout for on specific call by including a "rpc_timeout" kwarg in that call. For example dataInterface.getFile("BigFile", rpc_timeout=60). Note that before setting an RCP timeout you should check that the interface you are using is actually running over RPC because sometimes interfaces will run locally. To check that use the isRunningRemote() command, such as dataInterface.isRunningRemote(), see the openNeuroClient project for an example of this usage.

## **Some Alternate Configurations For Your Experiment**
### **Running everything on the same computer**
Start the projectInterface without the --dataRemote or --subjectRemote options. No need to start any other services, local versions of them will be created internally by the projectInterface.

    bash scripts/run-projectInterface.sh -p [your_project_name]

### **Running the subjectService remotely, but read DICOM data from the disk of the projectInterface computer**
Start the projectInterface only specifying --subjectRemote. Then start a subjectService on a different computer that will connect to the projectInterface. The scannerDataService will automatically be created internally by the projectInterface to read data from the projectInterface computer.

    bash scripts/run-projectInterface.sh -p [your_project_name] --subjectRemote

### **Reading both remote and local data**
Start the projectInterface with the --dataRemote option and connect to it with a scannerDataService from another computer. In addition create another instance of dataInterface() within your script specifying dataRemote=False. This second dataInterface can watch for DICOM files created locally and the remote dataInterface can get/put files to the remote scannerDataInterface (for example to write a text file with the classification results for use by PsychToolbox).

    dataInterface2 = DataInterface(dataRemote=False, allowedDirs=['*'], allowedFileTypes=['*'])
