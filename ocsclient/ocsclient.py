import urllib
import urllib2
import requests
import json
import base64
import os.path
import xml.etree.ElementTree as ET
import sys

class OCSClient(object):
    ns = {'conv_svc': 'http://schemas.dcs.nuance.com/conversionservice'}
    def __init__(self, stsUrl, poxEndpointUrl):
        self.stsUrl = stsUrl
        self.poxEndpointUrl = poxEndpointUrl
        self.proxy=None
        self.verifyPolicy = True

    def setProxy(self, proxyServer, portNo):
        self.proxy = {'https': proxyServer + ":" + str(portNo)}

    def setVerification(self, verification):
        self.verifyPolicy = verification

    def getCredential(self, name, password):
        self.name = name
        self.password = password
        request_values = {'wrap_name': name, 'wrap_password':password, 'wrap_scope':self.poxEndpointUrl}
        self.access_token = urllib.unquote(self.__server_request_post(self.stsUrl, request_values).partition("=")[2])

    def __server_request_post(self, url, requestParams):
        try:
            r = requests.post(url, data=requestParams, proxies=self.proxy, verify=self.verifyPolicy)
            return r.text
        except urllib2.HTTPError, e:
            print 'HTTP return code :', e.code
            print e.read()
            sys.exit(-1)

    def __server_request(self, url, requestParams):
        authStr = "WRAP access_token=\""+self.access_token+"\""
        myHeaders = {"Authorization": authStr, "Content-Type": "application/xml"}

        try:
            r = requests.get(url, params=requestParams, headers=myHeaders, proxies=self.proxy, verify=self.verifyPolicy)
            return r.text
        except urllib2.HTTPError, e:
            print 'HTTP return code :', e.code
            print e.read()
            sys.exit(-1)

    # Get Job Types
    def getJobTypes(self):
        url = self.poxEndpointUrl+"/GetJobTypes"
        jobTypesXml = self.__server_request(url, None)

        root = ET.fromstring(jobTypesXml)
        jobTypes = []
        for job in root.find('conv_svc:GetJobTypesResult', OCSClient.ns):
            jobTypeId = job.find('conv_svc:JobTypeId', OCSClient.ns).text
            description = job.find('conv_svc:Description', OCSClient.ns).text
            source = job.find('conv_svc:SourceFormat', OCSClient.ns).text
            target = job.find('conv_svc:TargetFormat', OCSClient.ns).text
            jobType = {}
            if(jobTypeId != '-1'):
                jobType['jobTypeId'] = jobTypeId
                jobType['description'] = description
                jobType['sourceFormat'] = source
                jobType['targetFormat'] = target
                jobTypes.append(jobType)
        return jobTypes

    # Create Job and return jobId
    def createJob(self, jobTypeId, title, description, metadata):
        url = self.poxEndpointUrl + "/CreateJob"
        request_values = {'jobTypeId': jobTypeId, 'title':title, 'description':description, 'metadata': metadata}
        createJobXml = self.__server_request(url, request_values)
        root = ET.fromstring(createJobXml)
        jobId = root.find('conv_svc:CreateJobResult', OCSClient.ns).text
        return jobId

    # GetUploadUrls
    def getUploadUrls(self, jobId, count):
        url = self.poxEndpointUrl + "/GetUploadUrls"
        request_values = {'jobId' : jobId, 'count': count}
        storeUrlsXml = self.__server_request(url, request_values)
        root = ET.fromstring(storeUrlsXml)
        storeUrls = []
        for url in root.find('conv_svc:GetUploadUrlsResult', OCSClient.ns):
            storeUrls.append(url.text)
        return storeUrls

    # Post Input File to Azure Storage
    def putInputFile(self, fileName, url):
        inputFile = open(fileName, "rb")
        inputData = inputFile.read()
        myHeaders ={
            'Content-Length': '%d' % len(inputData),
            'Content-Type' :'application/octet-stream',
            'x-ms-blob-type': 'BlockBlob'
        }
        r = requests.put(url, data=inputData, headers=myHeaders, proxies=self.proxy, verify=self.verifyPolicy)
        return r.text

    # Start Job
    def startJob(self, jobId, conversionParams):
        url = self.poxEndpointUrl + "/StartJob"
        request_values = {'jobId':jobId, 'timeToLiveSec': 3600, 'priority': 2, 'conversionParameters': conversionParams}
        self.__server_request(url, request_values)

    # Process on Call (Synchronous method)
    def processOnCall(self, jobId, conversionParams):
        url = self.poxEndpointUrl + "/ProcessOnCall"
        request_values = {'jobId':jobId, 'conversionParameters': conversionParams}
        response =  self.__server_request(url, request_values)
        root = ET.fromstring(response)
        processOnCallResult = []
        for url in root.find('conv_svc:ProcessOnCallResult', OCSClient.ns):
            processOnCallResult.append(url.text)
        return processOnCallResult

    # Get Job Info
    def getJobInfo(self, jobId):
        url = self.poxEndpointUrl + "/GetJobInfo"
        request_values = {'jobId':jobId}
        response =  self.__server_request(url, request_values)
        root = ET.fromstring(response)
        jobInfoResult = {}
        jobInfoResultXml = root.find('conv_svc:GetJobInfoResult', OCSClient.ns)
        jobInfoResult['completeness'] = jobInfoResultXml.find('conv_svc:Completeness', OCSClient.ns).text
        jobInfoResult['ended'] = jobInfoResultXml.find('conv_svc:Ended', OCSClient.ns).text
        jobInfoResult['estimatedWorkTime'] = jobInfoResultXml.find('conv_svc:EstimatedWorkTime', OCSClient.ns).text
        jobInfoResult['jobId'] = jobInfoResultXml.find('conv_svc:JobId', OCSClient.ns).text
        jobInfoResult['jobPriority'] = jobInfoResultXml.find('conv_svc:JobPriority', OCSClient.ns).text
        jobInfoResult['jobTypeId'] = jobInfoResultXml.find('conv_svc:JobTypeId', OCSClient.ns).text
        jobInfoResult['metadata'] = jobInfoResultXml.find('conv_svc:Metadata', OCSClient.ns).text
        jobInfoResult['pollInterval'] = jobInfoResultXml.find('conv_svc:PollInterval', OCSClient.ns).text
        jobInfoResult['processedPageCount'] = jobInfoResultXml.find('conv_svc:ProcessedPageCount', OCSClient.ns).text
        jobInfoResult['resultCode'] = jobInfoResultXml.find('conv_svc:ResultCode', OCSClient.ns).text
        jobInfoResult['resultMessage'] = jobInfoResultXml.find('conv_svc:ResultMessage', OCSClient.ns).text
        jobInfoResult['started'] = jobInfoResultXml.find('conv_svc:Started', OCSClient.ns).text
        jobInfoResult['state'] = jobInfoResultXml.find('conv_svc:State', OCSClient.ns).text

        return jobInfoResult

    # Get Download URLs
    def getDownloadUrls(self, jobId):
        url = self.poxEndpointUrl + '/GetDownloadUrls'
        requestParams = {'jobId': jobId}
        downloadUrls = self.__server_request(url, requestParams)

        root = ET.fromstring(downloadUrls)
        downloadUrls = []
        for url in root.find('conv_svc:GetDownloadUrlsResult', OCSClient.ns):
            downloadUrls.append(url.text)
        return downloadUrls

    # Store Result
    def downloadFile(self, url, fileName):
        r = requests.get(url, proxies=self.proxy, verify=self.verifyPolicy)
        localFile = open(fileName, 'wb')
        localFile.write(r.content)
        localFile.close()

    # Cancel Job
    def cancelJob(self, jobId):
        url = self.poxEndpointUrl + "/CancelJob"
        request_values = {'jobId':jobId}
        response =  self.__server_request(url, request_values)

    # Delete Job Data
    def deleteJobData(self, jobId, dataTypeFlag):
        url = self.poxEndpointUrl + "/DeleteJobData"
        request_values = {'jobId':jobId, 'dataTypeFlag':dataTypeFlag}
        response =  self.__server_request(url, request_values)
