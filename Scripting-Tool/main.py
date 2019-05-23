#!/usr/bin/python
import sys
import getopt
import tempfile
import requests
import os
import zipfile
import glob
import yaml
import json
from yaml import Loader

# Global Variables set by command line arguments in method main(argv).
GithubURL = ""
GithubDirectoryPath = ""
BioschemasURL = ""
SchemaURL = ""

# Additional Global Variables
TempWorkingDirectory = ""
TempWorkingDirectoryYAML = ""
ProfileJSONDefinitionDictionary = {}
ProfileJSONSchemaDictionary = {}
ProfileJSONTableDictionary = {}

# Default Definitions for form inputs
definitions = {
    "Boolean": {
        "type": "boolean"
    },
    "Date": {
        "type": "string"
    },
    "DateTime": {
        "type": "string"
    },
    "Integer": {
        "type": "integer"
    },
    "Number": {
        "type": "number"
    },
    "Text": {
        "type": "string",
        "format": "text"
    },
    "URL": {
        "type": "string",
        "format": "url"
    },
    "String": {
        "type": "string"
    }
}

# Property Ordering Priorities
propertyOrdering = {
    "Minimum": 1,
    "Recommended": 2,
    "Optional": 3
}


def main(argv):
    global GithubURL
    global GithubDirectoryPath
    global BioschemasURL
    global SchemaURL

    # Process Command Line Arguments
    try:
        opts, args = getopt.getopt(argv, "hg:d:b:s:", [
            "githuburl=", "githubdirectorypath=", "bioschemasurl=", "schemaurl="])
    except getopt.GetoptError:
        print("main.py -g <Github URL> -d <Github Directory Path> -b <Bioschemas URL> -s <Schema.org URL>")
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print(
                "main.py -g <Github URL> -d <Github Directory Path> -b <Bioschemas URL> -s <Schema.org URL>")
            sys.exit()
        elif opt in ("-g", "--githuburl"):
            GithubURL = arg
        elif opt in ("-d", "--githubdirectorypath"):
            GithubDirectoryPath = arg
        elif opt in ("-b", "--bioschemasurl"):
            BioschemasURL = arg
        elif opt in ("-s", "--schemaurl"):
            SchemaURL = arg

    # Check Command Line Arguments Exist
    if (not GithubURL or not GithubDirectoryPath or not BioschemasURL or not SchemaURL):
        print("Provide all arguments.")
        print("main.py -g <Github URL> -d <Github Directory Path> -b <Bioschemas URL> -s <Schema.org URL>")
        sys.exit(2)

    # Display Command Line Arguments
    print("Github URL: ", GithubURL)
    print("Github Directory Path: ", GithubDirectoryPath)
    print("Bioschemas URL: ", BioschemasURL)
    print("Schema.org URL: ", SchemaURL)

    # Transformation Process
    downloadGithubRepository()
    extractGithubRepositoryZip()
    extractYAML()
    convertYAML()
    processJSONDictionary()


def downloadGithubRepository():
    # Download Github repository specific by -g in the command line arguments
    global TempWorkingDirectory

    TempWorkingDirectory = tempfile.mkdtemp()

    # Download Github Repository Zip
    try:
        r = requests.get(GithubURL)
        with open(os.path.join(TempWorkingDirectory, 'bioschemas.zip'), 'wb') as f:
            f.write(r.content)
    except:
        print("Error: downloadGithubRepository")
        sys.exit(2)


def extractGithubRepositoryZip():
    # Extract Github Repository Zip into new folder
    try:
        with zipfile.ZipFile(TempWorkingDirectory + "/bioschemas.zip", "r") as zip_ref:
            zip_ref.extractall(TempWorkingDirectory)
    except:
        print("Error: extractGithubRepositoryZip")
        sys.exit(2)


def extractYAML():
    # Extract the YAML from the HTML files by specifiying the directory in the command line arguments using -d
    global TempWorkingDirectoryYAML

    TempWorkingDirectoryYAML = TempWorkingDirectory + "/yaml/"

    # Create TempWorkingDirectoryYAML
    if not os.path.exists(TempWorkingDirectoryYAML):
        os.makedirs(TempWorkingDirectoryYAML)

    htmlToProcess = glob.glob(
        TempWorkingDirectory + GithubDirectoryPath + "*.html")

    for htmlFile in htmlToProcess:
        try:
            htmlFileName = os.path.basename(htmlFile)
            profileName = os.path.splitext(htmlFileName)[0]
            newYAMLFile = TempWorkingDirectoryYAML + profileName + ".yaml"
            with open(htmlFile, "r", encoding="utf8") as input:
                with open(newYAMLFile, "w", encoding="utf8") as output:
                    seperatorCount = 0
                    for line in input:
                        if "---" == line.strip():
                            seperatorCount = seperatorCount + 1
                            if seperatorCount == 2:
                                break
                        output.write(line)
        except:
            print("Error: extractYAML")


def convertYAML():
    # Convert YAML into JSON objects to be further processed
    global ProfileJSONDefinitionDictionary

    yamlToProcess = glob.glob(TempWorkingDirectoryYAML + "*.yaml")

    for yamlFile in yamlToProcess:
        try:
            yamlFileName = os.path.basename(yamlFile)
            profileName = os.path.splitext(yamlFileName)[0]
            with open(yamlFile, "r", encoding="utf8") as input:
                ProfileJSONDefinitionDictionary[profileName] = yaml.load(
                    input, Loader=Loader)
        except:
            print("Error: convertYAML")


def processJSONDictionary():
    # For each definition create a JSON-Schema and JSON Table file
    for key, value in ProfileJSONDefinitionDictionary.items():
        try:
            print(key)
            ProfileJSONSchemaDictionary[key] = createJSONSchema(value)
            ProfileJSONTableDictionary[key] = createJSONTable(value)
        except:
            print("Error: processJSONDictionary")

    # Write JSON Dictionaries to file
    writeJSONFile(sys.path[0] + "/profiles/", ProfileJSONSchemaDictionary)
    writeJSONFile(sys.path[0] + "/tables/", ProfileJSONTableDictionary)


def createJSONSchema(definitionObject):
    # Create the JSON Schema describing a Bioschemas Profile
    schemaJSONObject = {}

    try:
        # Title / Version Number of Profile
        schemaJSONObject["title"] = definitionObject["spec_info"]["title"] + \
            " (v" + str(definitionObject["spec_info"]["version"]) + ")"
        # Description of Profile
        schemaJSONObject["description"] = definitionObject["spec_info"]["description"]
        # JSON Type
        schemaJSONObject["type"] = "object"

        # Properties of the Profile
        profilePropertiesObject = {}
        # Required Properties of the Profile
        profileRequiredProperties = []

        # Property definitions to generate for profile
        definitionsToGenerate = []

        # JSON-LD Context Attribute
        contextObject = {}
        contextObject["default"] = "http://schema.org"
        contextObject["type"] = "string"
        optionsObject = {}
        optionsObject["hidden"] = "true"
        contextObject["options"] = optionsObject
        profilePropertiesObject["@context"] = contextObject
        profileRequiredProperties.append("@type")

        # JSON-LD Type Attribute
        typeObject = {}
        typeObject["default"] = definitionObject["spec_info"]["title"]
        typeObject["options"] = optionsObject
        typeObject["type"] = "string"
        profilePropertiesObject["@type"] = typeObject
        profileRequiredProperties.append("@context")

        # Profile Properties
        for property in definitionObject["mapping"]:
            # Skip unnecessary types
            if property["property"] == "rdf:type":
                continue

            # Property Object
            tempPropertyObject = {}
            # Property Title / Marginality
            tempPropertyObject["title"] = property["property"] + \
                " (" + property["marginality"] + ")"

            # Property Ordering displated in form
            tempPropertyObject["propertyOrder"] = propertyOrdering[property["marginality"]]

            # Minimum Properties are required by default
            if property["marginality"].lower() == "minimum":
                profileRequiredProperties.append(property["property"])

            # Property Description
            concatenatedDescription = ""
            if property["bsc_description"]:
                concatenatedDescription = concatenatedDescription + \
                    "Bioschemas: " + property["bsc_description"] + " "
            if property["description"]:
                concatenatedDescription = concatenatedDescription + \
                    "Schema.org: " + property["description"] + " "
            tempPropertyObject["description"] = concatenatedDescription

            # Property Expected Types must be cleaned due to different formats
            expectedTypes = cleanDefinitions(property["expected_types"])
            # Cardinailty of the Property
            cardinality = property["cardinality"]

            # Add expected type of property to later generate
            oneOfArray = []
            for type in expectedTypes:
                addToArray(type, definitionsToGenerate)
                tempTypeObject = {}
                tempTypeObject["title"] = type
                tempTypeObject["$ref"] = "#/definitions/" + type
                oneOfArray.append(tempTypeObject)
            # Add oneOf array to property
            # If no cardinality is provided default to many
            if cardinality.lower() == "one":
                tempPropertyObject["oneOf"] = oneOfArray
            else:
                tempPropertyObject["type"] = "array"
                expectedTypeObject = {}
                expectedTypeObject["oneOf"] = oneOfArray
                tempPropertyObject["items"] = expectedTypeObject

            profilePropertiesObject[property["property"]] = tempPropertyObject

        # Generate Definitions needed for the Profile
        schemaJSONObject["definitions"] = generateDefinitions(
            definitionsToGenerate)
        # Add Properties Object to Schema
        schemaJSONObject["properties"] = profilePropertiesObject
        # Add Required Properties Array to Schema
        schemaJSONObject["required"] = profileRequiredProperties
    except:
        print("Error: createJSONSchema")

    return schemaJSONObject


def generateDefinitions(definitionsToGenerate):
    # print(definitionsToGenerate)

    for definition in definitionsToGenerate:
        pass
        # print(definition)

        # Check if in List of Bioschemas profiles
        # If type has profile use minimum version of profile

    # Check if in List of Bioschemas Types
        # If Bioschemas type create object

        # Else assume Schema.org type
        # Create @id for Schema.org Types

    return {}


def listOfBioschemasProfiles():
    #
    return []


def listOfBioschemasTypes():
    #
    return []


def generateBioschemasDefinition(definition):
    #
    print(definition)


def fetchSchemaDescription(definition):
    # Fetch the description of Schema.org types
    description = "No Description Available."

    try:
        r = requests.get(SchemaURL + definition + ".jsonld")
        jsonLD = json.loads(r.content.decode('utf-8'))

        for graph in jsonLD["@graph"]:
            if graph["@id"] == "schema:" + definition:
                description = graph["rdfs:comment"]
    except:
        print("Error: fetchSchemaDescription")

    return description



def cleanDefinitions(definitions):
    cleanDefinitions = []

    for definition in definitions:
        if (len(definition.split())) > 1:
            for tempProperty in definition.split():
                if tempProperty.lower().startswith("or"):
                    addToArray(tempProperty[2:], cleanDefinitions)
                elif tempProperty.startswith("bioschemas:"):
                    addToArray(tempProperty[11:], cleanDefinitions)
                else:
                    addToArray(tempProperty, cleanDefinitions)
        else:
            if definition.startswith("bioschemas:"):
                addToArray(definition[11:], cleanDefinitions)
            else:
                addToArray(definition, cleanDefinitions)

    return cleanDefinitions


def addToArray(string, array):
    # Only add unique items to array
    if string not in array:
        array.append(string)


def createJSONTable(definitionObject):
    # Create JSON object with additional information about property (example's and controlled vocabularies)
    tableJSONObject = {}

    try:
        for property in definitionObject["mapping"]:
            propertyObject = {}

            if property["example"]:
                propertyObject["example"] = property["example"]
            if property["controlled_vocab"]:
                propertyObject["controlled_vocab"] = property["controlled_vocab"]

            # If Property has additional information add to file
            if propertyObject:
                tableJSONObject[property["property"]] = propertyObject
    except:
        print("Error: createJSONTable")

    return tableJSONObject


def writeJSONFile(directory, JSONDictionary):
    # Write JSON Dictionary to JSON Files
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)

        for key, value in JSONDictionary.items():
            JSONFile = directory + key + ".json"
            with open(JSONFile, "w") as output:
                json.dump(value, output, indent=4, sort_keys=False)
    except:
        print("Error: writeJSON")


if __name__ == "__main__":
    main(sys.argv[1:])
