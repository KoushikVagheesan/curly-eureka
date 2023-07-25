import os
import shutil
import pefile
import hashlib
import array
import math
import socket
import numpy as np
import pandas as pd
from sklearn import metrics

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 1337
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

def xgboost():
  dataset1 = pd.read_csv('preddata.csv', sep = '|')
  X_pred= dataset1.drop(['Name', 'md5'], axis = 1).values
  dataset2 = pd.read_csv('data.csv', sep = '|')
  X = dataset2.drop(['Name', 'md5', 'legitimate'], axis = 1).values
  y = dataset2['legitimate'].values

# Splitting the dataset into the Training set and Test set
  from sklearn.model_selection import train_test_split
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.20, random_state = 0)

# Feature Scaling
  from sklearn.preprocessing import StandardScaler
  sc = StandardScaler()
  X_train = sc.fit_transform(X_train)
  X_test = sc.transform(X_test)

#Fitting xgboost to the training Set
  from xgboost import XGBClassifier
  classifier = XGBClassifier(max_depth=20, learning_rate=0.3, n_estimators=150)
  classifier.fit(X_train, y_train)

#predict the test results
  from sklearn import metrics
  y_pred1 = classifier.predict(X_test)
  print("Confusion Matrix=\n",metrics.confusion_matrix(y_test,y_pred1,labels=None,sample_weight=None))
  print("Recall:",metrics.recall_score(y_test,y_pred1,labels=None,pos_label=1,average='weighted',sample_weight=None))
  y_pred2 = classifier.predict(X_pred)
  
  from sklearn.model_selection import cross_val_score
  accuracies = cross_val_score(estimator = classifier, X = X_train, y = y_train, cv = 8)
  print(y_pred2)
  print("Accuracy of the model is:",accuracies.mean()*100,"%")
  print("Standard deviation between data is:",accuracies.std())
  return y_pred2[0] 
  
  
def get_md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_entropy(data):
  if len(data) == 0:
     return 0.0
  occurences = array.array('L', [0]*256)
  for x in data:
     occurences[x if isinstance(x, int) else ord(x)]+=1

  entropy = 0
  for x in occurences:
   if x:
     p_x=float(x)/len(data)
     entropy-=p_x*math.log(p_x, 2)

  return entropy

def get_resources(pe):
    resources = []
    if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
     try:
       for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if hasattr(resource_type, 'directory'):
         for resource_id in resource_type.directory.entries:
           if hasattr(resource_id, 'directory'):
             for resource_lang in resource_id.directory.entries:
                      data = pe.get_data(resource_lang.data.struct.OffsetToData, resource_lang.data.struct.Size)
                      size = resource_lang.data.struct.Size
                      entropy = get_entropy(data)

                      resources.append([entropy, size])
     except Exception as e:
       return resources
    return resources

def get_version_info(pe):
 """return version info"""
 res={}
 for fileinfo in pe.FileInfo:
  if fileinfo.Key=='StringFileInfo':
    for st in fileinfo.StringTable:
      for entry in st.entries.items():
        res[entry[0]]=entry[1]
  if fileinfo.Key=='VarFileInfo':
    for var in fileinfo.Var:
      res[var.entry.items()[0][0]]=var.entry.items()[0][1]
 if hasattr(pe, 'VS_FIXEDFILEINFO'):
  res['flags']=pe.VS_FIXEDFILEINFO.FileFlags
  res['os']=pe.VS_FIXDFILEINFO.FileOS
  res['type']=pe.VS_FIXEDFILEINFO.FileType
  res['file_version']=pe.VS_FIXEDFILEINFO.FileVersionLS                         
  res['product_version'] = pe.VS_FIXEDFILEINFO.ProductVersionLS
  res['signature'] = pe.VS_FIXEDFILEINFO.Signature
  res['struct_version'] = pe.VS_FIXEDFILEINFO.StrucVersion 

 return res          

def extract_infos(fpath):
    res=[]
    res.append(os.path.basename(fpath))
    res.append(get_md5(fpath))
    pe = pefile.PE(fpath)
    res.append(pe.FILE_HEADER.Machine)
    res.append(pe.FILE_HEADER.SizeOfOptionalHeader)
    res.append(pe.FILE_HEADER.Characteristics)
    res.append(pe.OPTIONAL_HEADER.MajorLinkerVersion)
    res.append(pe.OPTIONAL_HEADER.MinorLinkerVersion)
    res.append(pe.OPTIONAL_HEADER.SizeOfCode)
    res.append(pe.OPTIONAL_HEADER.SizeOfInitializedData)
    res.append(pe.OPTIONAL_HEADER.SizeOfUninitializedData)
    res.append(pe.OPTIONAL_HEADER.AddressOfEntryPoint)
    res.append(pe.OPTIONAL_HEADER.BaseOfCode)
    try:
     res.append(pe.OPTIONAL_HEADER.BaseOfData)
    except AttributeError:
     res.append(0)
    res.append(pe.OPTIONAL_HEADER.ImageBase)
    res.append(pe.OPTIONAL_HEADER.SectionAlignment)
    res.append(pe.OPTIONAL_HEADER.FileAlignment)
    res.append(pe.OPTIONAL_HEADER.MajorOperatingSystemVersion)
    res.append(pe.OPTIONAL_HEADER.MinorOperatingSystemVersion)
    res.append(pe.OPTIONAL_HEADER.MajorImageVersion)
    res.append(pe.OPTIONAL_HEADER.MinorImageVersion)
    res.append(pe.OPTIONAL_HEADER.MajorSubsystemVersion)
    res.append(pe.OPTIONAL_HEADER.MinorSubsystemVersion)
    res.append(pe.OPTIONAL_HEADER.SizeOfImage)
    res.append(pe.OPTIONAL_HEADER.SizeOfHeaders)
    res.append(pe.OPTIONAL_HEADER.CheckSum)
    res.append(pe.OPTIONAL_HEADER.Subsystem)
    res.append(pe.OPTIONAL_HEADER.DllCharacteristics)
    res.append(pe.OPTIONAL_HEADER.SizeOfStackReserve)
    res.append(pe.OPTIONAL_HEADER.SizeOfStackCommit)
    res.append(pe.OPTIONAL_HEADER.SizeOfHeapReserve)
    res.append(pe.OPTIONAL_HEADER.SizeOfHeapCommit)
    res.append(pe.OPTIONAL_HEADER.LoaderFlags)
    res.append(pe.OPTIONAL_HEADER.NumberOfRvaAndSizes)
    res.append(len(pe.sections))
    entropy = list(map(lambda x:x.get_entropy(), pe.sections))
    res.append(sum(entropy)/float(len(entropy)))
    res.append(min(entropy))
    res.append(max(entropy))
    raw_sizes =list(map(lambda x:x.SizeOfRawData, pe.sections))
    res.append(sum(raw_sizes)/float(len(raw_sizes)))
    res.append(min(raw_sizes))
    res.append(max(raw_sizes))
    virtual_sizes = list(map(lambda x:x.Misc_VirtualSize, pe.sections))
    res.append(sum(virtual_sizes)/float(len(virtual_sizes)))
    res.append(min(virtual_sizes))
    res.append(max(virtual_sizes))
    #Imports
    try:
        res.append(len(pe.DIRECTORY_ENTRY_IMPORT))
        imports = sum([x.imports for x in pe.DIRECTORY_ENTRY_IMPORT], [])
        res.append(len(imports))
        res.append(len(list(filter(lambda x:x.name is None, imports))))
    except AttributeError:
        res.append(0)
        res.append(0)
        res.append(0)
    #Exports
    try:
        res.append(len(pe.DIRECTORY_ENTRY_EXPORT.symbols))
    except AttributeError:
        # No export
        res.append(0)
    #Resources
    resources= get_resources(pe)
    res.append(len(resources))
    if len(resources)> 0:
        entropy =list( map(lambda x:x[0], resources))
        res.append(sum(entropy)/float(len(entropy)))
        res.append(min(entropy))
        res.append(max(entropy))
        sizes =list(map(lambda x:x[1], resources))
        res.append(sum(sizes)/float(len(sizes)))
        res.append(min(sizes))
        res.append(max(sizes))
    else:
        res.append(0)
        res.append(0)
        res.append(0)
        res.append(0)
        res.append(0)
        res.append(0)

    # Load configuration size
    try:
        res.append(pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct.Size)
    except AttributeError:
        res.append(0)

    # Version configuration size
    try:
        version_infos = get_version_info(pe)
        res.append(len(version_infos.keys()))
    except AttributeError:
        res.append(0)
    return res


def extract(filename):
    ffile=filename
    output = "preddata.csv"
    csv_delimiter = "|"
    columns = [
        "Name",
        "md5",
        "Machine",
        "SizeOfOptionalHeader",
        "Characteristics",
        "MajorLinkerVersion",
        "MinorLinkerVersion",
        "SizeOfCode",
        "SizeOfInitializedData",
        "SizeOfUninitializedData",
        "AddressOfEntryPoint",
        "BaseOfCode",
        "BaseOfData",
        "ImageBase",
        "SectionAlignment",
        "FileAlignment",
        "MajorOperatingSystemVersion",
        "MinorOperatingSystemVersion",
        "MajorImageVersion",
        "MinorImageVersion",
        "MajorSubsystemVersion",
        "MinorSubsystemVersion",
        "SizeOfImage",
        "SizeOfHeaders",
        "CheckSum",
        "Subsystem",
        "DllCharacteristics",
        "SizeOfStackReserve",
        "SizeOfStackCommit",
        "SizeOfHeapReserve",
        "SizeOfHeapCommit",
        "LoaderFlags",
        "NumberOfRvaAndSizes",
        "SectionsNb",
        "SectionsMeanEntropy",
        "SectionsMinEntropy",
        "SectionsMaxEntropy",
        "SectionsMeanRawsize",
        "SectionsMinRawsize",
        "SectionMaxRawsize",
        "SectionsMeanVirtualsize",
        "SectionsMinVirtualsize",
        "SectionMaxVirtualsize",
        "ImportsNbDLL",
        "ImportsNb",
        "ImportsNbOrdinal",
        "ExportNb", 
        "ResourcesNb",
        "ResourcesMeanEntropy",
        "ResourcesMinEntropy",
        "ResourcesMaxEntropy",
        "ResourcesMeanSize",
        "ResourcesMinSize",
        "ResourcesMaxSize",
        "LoadConfigurationSize",
        "VersionInformationSize"
    ]

    ff = open(output,"a")
    ff.write(csv_delimiter.join(columns) + "\n")
    
    # Launch legitimate
    try:
      res = extract_infos(os.path.join("recfile/",ffile)) #extracts data required for model input from pefile
      ff.write(csv_delimiter.join(map(lambda x:str(x), res)) + "\n")
      print("Infos Extracted")
    except pefile.PEFormatError as e:
      print(e)
    
def main():
   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   s.bind(("localhost", SERVER_PORT))
   s.listen(5)
   print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
   client_socket, address = s.accept() 
# if below code is executed, that means the sender is connected
   print(f"[+] {address} is connected.")
   file = open("recfile/rcv.exe","wb")
   print("Waiting for file: ")
   file.write(client_socket.recv(1024*1024*5))
   file.close()
   print("File has been received")
   extract("rcv.exe")
   client_socket.send(str(xgboost()).encode())
   print("Result sent")
   os.system("rm preddata.csv recfile/rcv.exe") #deleting the received file and data extracted from that file
main()

   
