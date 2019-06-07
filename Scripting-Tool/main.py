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

# Global Variables set by command line arguments in main method
GithubURL = ""
GithubDirectoryPath = ""
GithubTypePath = ""
BioschemasURL = ""
SchemaURL = ""

# Additional Global Variables
TempWorkingDirectory = ""
TempWorkingDirectoryYAML = ""
ProfileJSONDefinitionDictionary = {}
ProfileJSONSchemaDictionary = {}
ProfileJSONTableDictionary = {}
ProfileMinimumDefinitionDictionary = {}
ListOfBioschemasProfiles = []
ListOfBioschemasTypes = []

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
    global GithubTypePath
    global BioschemasURL
    global SchemaURL

    # Process Command Line Arguments
    try:
        opts, args = getopt.getopt(argv, "hg:d:t:b:s:", [
            "githuburl=", "githubdirectorypath=", "githubtypepath=", "bioschemasurl=", "schemaurl="])
    except getopt.GetoptError:
        print("main.py -g <Github URL> -d <Github Profiles Directory Path>  -t <Github Types Directory Path> -b <Bioschemas URL> -s <Schema.org URL>")
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            print(
                "main.py -g <Github URL> -d <Github Profiles Directory Path> -t <Github Types Directory Path> -b <Bioschemas URL> -s <Schema.org URL>")
            sys.exit()
        elif opt in ("-g", "--githuburl"):
            GithubURL = arg
        elif opt in ("-d", "--githubdirectorypath"):
            GithubDirectoryPath = arg
        elif opt in ("-t", "--githubtypepath"):
            GithubTypePath = arg
        elif opt in ("-b", "--bioschemasurl"):
            BioschemasURL = arg
        elif opt in ("-s", "--schemaurl"):
            SchemaURL = arg

    # Check Command Line Arguments Exist
    if (not GithubURL or not GithubDirectoryPath or not BioschemasURL or not SchemaURL or not GithubTypePath):
        print("Provide all arguments.")
        print("main.py -g <Github URL> -d <Github Profiles Directory Path> -t <Github Types Directory Path> -b <Bioschemas URL> -s <Schema.org URL>")
        sys.exit(2)

    # Display Command Line Arguments
    print("Github URL: ", GithubURL)
    print("Github Profiles Path: ", GithubDirectoryPath)
    print("Github Types Path: ", GithubTypePath)
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
    # Get List of Profiles and List of Types for Bioschemas
    listOfBioschemasProfiles()
    listOfBioschemasTypes()

    # For each definition create a JSON-Schema and JSON Table file
    for key, value in ProfileJSONDefinitionDictionary.items():
        try:
            print(key)
            ProfileJSONSchemaDictionary[key] = createJSONSchema(value)
            ProfileJSONTableDictionary[key] = createJSONTable(value)
        except:
            print("Error: processJSONDictionary")

    # Add minimum definitions for profiles
    #addMinimumDefinitions()

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
        optionsObject = {}
        optionsObject["hidden"] = "true"
        contextObject["options"] = optionsObject
        contextObject["type"] = "string"
        profilePropertiesObject["@context"] = contextObject
        profileRequiredProperties.append("@type")

        # JSON-LD Type Attribute
        typeObject = {}
        typeObject["default"] = definitionObject["spec_info"]["title"]
        typeObject["options"] = optionsObject
        typeObject["type"] = "string"
        profilePropertiesObject["@type"] = typeObject
        profileRequiredProperties.append("@context")

        # dct:conformsTo
        dctObject = {}
        dctObject["default"] = "https://bioschemas.org/specifications/" + \
            definitionObject["spec_info"]["title"] + "/" + \
            str(definitionObject["spec_info"]["version"])
        dctObject["options"] = optionsObject
        dctObject["type"] = "string"
        profilePropertiesObject["dct:conformsTo"] = dctObject
        profileRequiredProperties.append("dct:conformsTo")

        # Profile Properties
        for property in definitionObject["mapping"]:
            # Skip unnecessary property
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

            # Order oneOf Array so that Text is first in the list and therefore default
            for index, item in enumerate(oneOfArray.copy()):
                if item["title"] == "Text":
                    if index == 0:
                        break
                    else:
                        oneOfArray.insert(0, oneOfArray.pop(index))

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
    profileDefinitions = definitions.copy()

    for definition in definitionsToGenerate:

        if definition in ListOfBioschemasProfiles:
            # If type has profile use minimum version of profile
            # Added at the end
            profileDefinitions[definition] = {}
        elif definition in ListOfBioschemasTypes:
            # If Bioschemas type create object
            profileDefinitions[definition] = generateBioschemasDefinition(
                definition)
        elif definition not in definitions:
            # Else assume Schema.org type
            # Create @id for Schema.org Types
            profileDefinitions[definition] = generateSchemaDefinition(
                definition)

    return profileDefinitions


def generateBioschemasDefinition(definition):

    try:
        definitionObject = fetchBioschemaDefinition(definition)
        definitionSchema = {}
        schemaProperties = {}
        requiredProperties = []

        # Title of Bioschemas Type
        definitionSchema["title"] = definition

        # JSON-LD Context Attribute
        contextObject = {}
        contextObject["default"] = "http://schema.org"
        contextObject["type"] = "string"
        optionsObject = {}
        optionsObject["hidden"] = "true"
        contextObject["options"] = optionsObject
        schemaProperties["@context"] = contextObject
        requiredProperties.append("@context")

        # JSON-LD Type Attribute
        typeObject = {}
        typeObject["default"] = definition
        typeObject["options"] = optionsObject
        typeObject["type"] = "string"
        schemaProperties["@type"] = typeObject
        requiredProperties.append("@type")

        for graph in definitionObject["@graph"]:
            # Bioschemas Type Description
            try:
                if graph["@id"] == "schema:" + definition and graph["@type"] == "rdfs:Class":
                    definitionSchema["description"] = graph["rdfs:comment"]
            except:
                print("Error, generateBioschemasDefinition Description")

            # Bioschemas Properties
            try:
                if "@type" in graph:
                    if graph["@type"] == "rdf:Property":
                        propertyObject = {}
                        propertyObject["title"] = graph["@id"][7:]
                        propertyObject["description"] = graph["rdfs:comment"]
                        # Default to cardinality of MANY
                        propertyObject["type"] = "array"
                        oneOfArray = []

                        # Convert rangeIncludes to always be an array to be proccessed easily
                        rangeIncludes = []
                        if isinstance(graph["schema:rangeIncludes"], list):
                            rangeIncludes = rangeIncludes + \
                                graph["schema:rangeIncludes"]
                        else:
                            rangeIncludes.append(graph["schema:rangeIncludes"])

                        for type in rangeIncludes:
                            typeObject = {}
                            if type["@id"][7:] in definitions:
                                typeObject["title"] = type["@id"][7:]
                                typeObject["$ref"] = "#/definitions/" + \
                                    type["@id"][7:]
                            else:
                                typeObject["title"] = type["@id"][7:]
                                typeProperties = {}
                                typeContextObject = {}
                                typeContextObject["default"] = type["@id"][7:]
                                typeOptionsObject = {}
                                typeOptionsObject["hidden"] = "true"
                                typeContextObject["options"] = typeOptionsObject
                                typeContextObject["type"] = "string"
                                typeProperties["@type"] = typeContextObject

                                identifierObject = {}
                                identifierObject["title"] = "Link to other resource"
                                identifierObject["description"] = "Placeholder Description"
                                identifierObject["$ref"] = "#/definitions/URL"
                                typeProperties["@id"] = identifierObject

                                typeObject["properties"] = typeProperties
                                typeObject["required"] = ["@type", "@id"]

                            oneOfArray.append(typeObject)

                        # Order oneOf Array so that Text is first in the list and therefore default
                        for index, item in enumerate(oneOfArray.copy()):
                            if item["title"] == "Text":
                                if index == 0:
                                    break
                                else:
                                    oneOfArray.insert(0, oneOfArray.pop(index))

                        propertyObject["items"] = {"oneOf": oneOfArray}
                        schemaProperties[graph["@id"][7:]] = propertyObject

            except:
                print("Error, generateBioschemasDefinition Properties")

        definitionSchema["properties"] = schemaProperties
        definitionSchema["required"] = requiredProperties

        return definitionSchema

    except:
        print("Error: generateBioschemasDefinition")


def generateSchemaDefinition(definition):

    schemaDefinition = {}

    schemaDefinition["title"] = definition
    schemaDefinition["description"] = fetchSchemaDescription(definition)

    schemaProperties = {}

    contextObject = {}
    contextObject["default"] = definition
    contextObject["type"] = "string"
    optionsObject = {}
    optionsObject["hidden"] = "true"
    contextObject["options"] = optionsObject
    schemaProperties["@type"] = contextObject

    identifierObject = {}
    identifierObject["title"] = "Link to other resource"
    identifierObject["description"] = "Placeholder Description"
    identifierObject["$ref"] = "#/definitions/URL"
    schemaProperties["@id"] = identifierObject

    schemaDefinition["properties"] = schemaProperties

    schemaDefinition["required"] = ["@id", "@type"]

    return schemaDefinition


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

            # If Property has additional information add to JSON file output
            if propertyObject:
                tableJSONObject[property["property"]] = propertyObject
    except:
        print("Error: createJSONTable")

    return tableJSONObject


def addMinimumDefinitions(schemaDictionary,minimumDictionary):
    pass


def listOfBioschemasProfiles():
    global ListOfBioschemasProfiles
    bioschemasProfilesDirectory = TempWorkingDirectory + GithubDirectoryPath
    tempListOfProfiles = glob.glob(bioschemasProfilesDirectory + "*.html")

    for profile in tempListOfProfiles:
        htmlFileName = os.path.basename(profile)
        profileName = os.path.splitext(htmlFileName)[0]
        ListOfBioschemasProfiles.append(profileName)


def listOfBioschemasTypes():
    global ListOfBioschemasTypes

    bioschemasTypesDirectory = TempWorkingDirectory + GithubTypePath
    tempListOfTypes = glob.glob(bioschemasTypesDirectory + "*.html")

    for type in tempListOfTypes:
        htmlFileName = os.path.basename(type)
        typeName = os.path.splitext(htmlFileName)[0]
        ListOfBioschemasTypes.append(typeName)


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


def fetchBioschemaDefinition(definition):
    try:
        r = requests.get(BioschemasURL + definition + ".jsonld")
        return json.loads(r.content.decode('utf-8'))
    except:
        print("Error: fetchBioschemaDefinition")


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
