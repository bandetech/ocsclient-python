from ocsclient import ocsclient

print 'OmniPage Cloud Service Client Demo'

stsEndpoint = 'https://nuance-sts.nuancecomputing.com/issue/wrap/WRAPv0.9'
poxEndpoint = 'https://dcs-ncus.nuancecomputing.com/ConversionService.svc/pox'

# Please set your account name and account Key here. Please refer https://portal.nuancecomputing.com/my-account-items

account_name = '<YOUR ACCOUNT NAME>'
account_key  = '<YOUR ACCOUNT KEY>'

# Please specify file path for input Image and output file
inputImage = "<INPUT FILE PATH HERE>"
outputFile = "<OUTPUT FILE PATH HERE>"

client = ocsclient.OCSClient(stsEndpoint, poxEndpoint)

# If your environment has proxy, please set your proxy server and port number here.
#client.setProxy('<hostname>', <portnum>)

client.getCredential(account_name, account_key)

print client.getJobTypes()
jobId = client.createJob(18, "test", "python test", None)
uploadUrls = client.getUploadUrls(jobId, 1)
client.putInputFile(inputImage, uploadUrls[0])

conversionParams = ('<ConversionParameters xmlns="http://www.nuance.com/2011/ConversionParameters">'
'<ImageQuality>Better</ImageQuality>'
'<LogicalFormRecognition>No</LogicalFormRecognition>'
'<Language>LANG_JPN</Language>'
'<Rotation>Auto</Rotation>'
'<Deskew>No</Deskew>'
'<TradeOff>Balanced</TradeOff>'
'<LayoutTradeOff>Accuracy</LayoutTradeOff>'
'<PDFCompatibility>PDF1.6</PDFCompatibility>'
'<CacheInputForReuse>True</CacheInputForReuse>'
'</ConversionParameters>')

print 'Calling synchronous process...'
print client.processOnCall(jobId, conversionParams)

print 'Process end. Downloading file...'
downloadUrls =  client.getDownloadUrls(jobId)
client.downloadFile(downloadUrls[0], outputFile)
