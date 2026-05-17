# Save model file and dependencies, args, kwargs, creation date, input and output shapes
import torch
import os
import shutil
import json
from os import listdir
from os.path import isfile, join
import importlib
import importlib.util
import sys


def import_from_path(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    print(f'module_name {module_name} path {path} spec {spec}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

class PortableTorch():
    cnt = 0 # static
    def __init__(self,model,model_class_name,modelsrc_path,dependence_paths=[],args=[],kwargs={},input_shape=None,output_shape=None,comment=""):
        self.model = model
        self.modelsrc_path = modelsrc_path
        self.modelsrc_filename = os.path.basename(self.modelsrc_path)
        self.dependence_paths = dependence_paths
        self.info = {"modelsrc_filename":self.modelsrc_filename,"model_class_name":model_class_name,"args":args,"kwargs":kwargs,"input_shape":input_shape,"output_shape":output_shape,"comment":comment}

    def save(self, dirpath):
        def _copy_force(path1,path2):
            try:
                shutil.copy(path1, path2)
            except shutil.SameFileError:
                pass
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        _copy_force(self.modelsrc_path, dirpath)
        for filepath in self.dependence_paths:
            _copy_force(filepath, dirpath)
        fp = open(dirpath+"/info.json","w")
        fp.write(json.dumps(self.info))
        torch.save(self.model.state_dict(),dirpath+"/model.pt")

    def print(self):
       print(f'{self.info["comment"]} input shape {self.info["input_shape"]} output shape {self.info["output_shape"]}')

    def test(self):
        input = torch.rand( self.info["input_shape"] )
        with torch.no_grad():
            output = self.model(input)
        print(f'input {input} resulted in output {output}')
        
    @staticmethod
    def load(dirpath):
        # Add to beginning of path so some other file(s)
        #   with the same name isn't loaded instead

        fp = open(dirpath+"/info.json","r")
        string = fp.read()
        info = json.loads(string)

        deps = []
        allfiles = [f for f in listdir(dirpath) if isfile(join(dirpath, f))]
        for filename in allfiles:
            if filename == info["modelsrc_filename"]:
                class_module = import_from_path(filename[-3:]+str(PortableTorch.cnt),dirpath+"/"+filename)
                PortableTorch.cnt += 1
            #elif filename[-3:]==".py": # Delete??
            #    dep_name = filename[:-3]
            #    importlib.import_module(dirpath+"/"+dep)
            #    deps.append(dirpath+"/"+dep)
            elif filename[-3:]==".pt":
                weight_filename = filename
        class_ = getattr(class_module, info["model_class_name"])
        # Use constructor to initialize model, then load weights
        model = class_(*info["args"],**info["kwargs"])
        map_location = None
        if not torch.cuda.is_available():
            map_location=torch.device('cpu')
        model.load_state_dict(torch.load(dirpath+"/"+weight_filename, map_location=map_location))
        model.eval()
        portable = PortableTorch(
            model,
            info["model_class_name"],
            dirpath+"/"+info["modelsrc_filename"],
            deps,
            info["args"],
            info["kwargs"],
            info["input_shape"],
            info["output_shape"],
            info["comment"]
        )
        return portable
