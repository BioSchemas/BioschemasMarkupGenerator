#!/usr/bin/python
import sys
import getopt
import tempfile
import requests
import os
import zipfile
import glob
import yaml
import configparser
import json
from yaml import Loader


GithubURL = ""
CurrentProfilesDirectoryPath = ""
CurrentTypesDirectoryPath = ""
DraftProfilesDirectoryPath = ""
DraftTypesDirectoryPath = ""
BioschemasURL = ""
SchemaURL = ""

def main(args):
    global GithubURL
    global CurrentProfilesDirectoryPath
    global CurrentTypesDirectoryPath
    global DraftProfilesDirectoryPath
    global DraftTypesDirectoryPath
    global BioschemasURL
    global SchemaURL

    try:
        config = configparser.ConfigParser()
        config.read("ConfigFile.ini")

        GithubURL = config.get("Github","url")
        CurrentProfilesDirectoryPath = config.get("Github","currentProfilesDirectoryPath")
        CurrentTypesDirectoryPath = config.get("Github","currentTypesDirectoryPath")
        DraftProfilesDirectoryPath = config.get("Github","draftProfilesDirectoryPath")
        DraftTypesDirectoryPath = config.get("Github","draftTypesDirectoryPath")
        BioschemasURL = config.get("Bioschemas","url")
        SchemaURL = config.get("SchemaOrg","url")

        print("Github URL: ", GithubURL)
        print("Github Current Profiles Path: ", CurrentProfilesDirectoryPath)
        print("Github Current Types Path: ", CurrentTypesDirectoryPath)
        print("Github Draft Profiles Path: ", DraftProfilesDirectoryPath)
        print("Github Draft Types Path: ", DraftTypesDirectoryPath)
        print("Bioschemas URL: ", BioschemasURL)
        print("Schema.org URL: ", SchemaURL)

    except:
        print("Error: main")
        print("Provide all arguments through ConfigFile.ini")
        sys.exit(2)

if __name__ == "__main__":
    main(sys.argv[1:])
