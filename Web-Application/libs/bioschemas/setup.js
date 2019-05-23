//GLOBAL VARIABLES
var editor;
var dropdownArray = new Array();
//JSON Editor Settings
JSONEditor.defaults.theme = 'bootstrap4';
JSONEditor.defaults.options["display_required_only"] = true;
JSONEditor.defaults.options["disable_collapse"] = true;
JSONEditor.defaults.options["disable_edit_json"] = true;
JSONEditor.defaults.options["keep_oneof_values"] = false;
//Bioschemas Generator Setup Functions:

//When dropdown is ready initalise Bioschemas Generator
$("#profileDropDown").ready(function () {
    initialise();
});

//Initalise Bioschemas Generator
function initialise() {
    console.log("Initalise Bioschemas Generator");
    listOfFiles();
}

//Fetch list of JSON files
function listOfFiles() {
    //Get list of JSON Schema files
    var fileNames = new Array();
    $.ajax({
        url: "/~st24/profiles/",
        success: function (data) {
            $(data).find("td > a").each(function () {
                //If file is a JSON Schema file add to list
                if ((/\.(json)$/i).test($(this).attr("href"))) {
                    fileNames.push($(this).attr("href"));
                }
            });
        },
        complete: function () {
            //Process JSON Schema Files
            console.log(fileNames);
            processJSONSchema(fileNames);
        }
    });
}

//Process JSON Schema FIles
function processJSONSchema(fileNames){

    for (i = 0; i< fileNames.length; i++){
        $.ajax({
            type: "Get",
            url: "http://www2.macs.hw.ac.uk/~st24/profiles/" + fileNames[i],
            dataType: "json",
            success: function(data) {
                tableUrl = this.url.replace("profiles","tables");
                tableUrl = tableUrl.replace(".json", "-Table.json");
                console.log(tableUrl);
                processAdditionalJSON(data,tableUrl);
            },
            error: function(){
                console.log("JSON Schema not found");
            }
        });
    }   
}

//Process Additional Information
function processAdditionalJSON(jsonSchema,fileName){
    console.log(fileName);
    $.ajax({
        type: "Get",
        url: fileName ,
        dataType: "json",
        success: function(data) {
            addOptionToDropDown(jsonSchema,data);
        },
        error: function(){
            console.log("JSON Schema not found");
        }
    });  
}

//Add Option to Dropdown
function addOptionToDropDown(jsonSchema,additionalJSON){
    var dropdown = document.getElementById("profileDropDown");
    var option = document.createElement("OPTION");
    console.log(jsonSchema);
    option.innerHTML = jsonSchema["title"];
    option.value = JSON.stringify(jsonSchema);
    option.setAttribute("data-json", JSON.stringify(additionalJSON));
    dropdown.options.add(option);
}

//Generate Form and Display Additional Info
function generateForm(){
    var dropDown =  document.getElementById("profileDropDown"); 
    var profileValue = dropDown.value;
    if(profileValue != "NULL"){
        if(editor){
           editor.destroy();
        }
        editor = new JSONEditor(document.getElementById('editor_holder'),{"schema":JSON.parse(profileValue)});
    }

    var additionalValue = dropDown.options[dropDown.selectedIndex].dataset.json;
    jsonToTable(JSON.parse(additionalValue));

    $("#collapseTwo").tab('show');
}

//JSON TO TABLE
function jsonToTable(jsonTable){
    
    //Minimum
    //Property
        // Example
        // Vocab
    //Recommended
    //Optional
    
    var gridContainer = document.getElementById("grid-container");
    var formArea = document.getElementById("form-area");
    var tipArea = document.getElementById("tip-area");
    var tipTitle = document.getElementById("tipTitle");
    var minimumDiv = document.getElementById("minimumDiv");
    minimumDiv.innerHTML = "";
    var recommendedDiv = document.getElementById("recommendedDiv");
    recommendedDiv.innerHTML = "";
    var optionalDiv = document.getElementById("optionalDiv");
    optionalDiv.innerHTML = "";

    var minimumItems = 0;
    var recommendedItems = 0;
    var optionalItems = 0;

    if (!jQuery.isEmptyObject(jsonTable)){
        gridContainer.setAttribute("class", "grid-container"); 
        formArea.setAttribute("class", "form-area"); 
        tipArea.setAttribute("class", "tip-area"); 
        tipArea.style.display = "block";
        tipTitle.style.display = "block";

        //Sort json object alphabtically
        const ordered = {};
        Object.keys(jsonTable).sort().forEach(function(key) {
            ordered[key] = jsonTable[key];
        });
        
        $.each(ordered, function( key, value ) {
            var div = document.createElement("div");

            var heading = document.createElement("h6");
            heading.innerHTML = key;
            div.appendChild(heading);
            
            
            if ('example' in value){
                exampleDiv = document.createElement("div");
                exampleDiv.innerHTML = "Example: ";
                link = document.createElement("a");
                link.href = "#"
                link.onclick = function(){
                    displayModal(key,value["example"]);
                }
                link.innerHTML = "Show";
                exampleDiv.appendChild(link);
                div.appendChild(exampleDiv);
            }

            if ('controlled_vocab' in value){
                controlledVocabDiv = document.createElement("div");
                controlledVocabDiv.innerHTML = "Controlled Vocabulary: " + value["controlled_vocab"];
                div.appendChild(controlledVocabDiv);
            }         

            marginality = value["marginality"];
            if (marginality.toLowerCase() === "minimum" ){
                minimumDiv.appendChild(div);
                minimumItems += 1;
            }else if (marginality.toLowerCase() === "recommended" ){
                recommendedDiv.appendChild(div);
                recommendedItems +=1 ;
            }else if (marginality.toLowerCase() === "optional" ){
                optionalDiv.appendChild(div);
                optionalItems +=1;
            }
        });    

        if (minimumItems == 0){
            var minimumAccordion = document.getElementById("minimumAccordion");
            minimumAccordion.style.display = "none";
        }
        if (recommendedItems == 0){
            var recommendedAccordion = document.getElementById("recommendedAccordion");
            recommendedAccordion.style.display = "none";
        }
        if (optionalItems == 0){
            var optionalAccordion = document.getElementById("optionalAccordion");
            optionalAccordion.style.display = "none";
        }

    }else{
        gridContainer.setAttribute("class", ""); 
        formArea.setAttribute("class", ""); 
        tipArea.setAttribute("class", ""); 
        tipArea.style.display = "none";
    }
}

//Display generated Markup
function generateMarkup(){
    jsonEditorOutput = JSON.stringify(editor.getValue(),null,2);
    
    document.getElementById('json-ld').innerHTML = '&lt;script type="application/ld+json" &gt;\n' + jsonEditorOutput + "\n&lt;/script &gt;";

    jsonldToRDFa(editor.getValue());
    jsonldToMicrodata(editor.getValue());

    $("#collapseThree").tab('show');
}

//Convert JSON to RDFa
function jsonldToRDFa(jsonld) {
    jsonldString = JSON.stringify(jsonld);
    postString = "content=" + jsonldString;

    $.ajax({
        url: 'http://rdf-translator.appspot.com/convert/json-ld/rdfa/content',
        type: 'post',
        data: postString,
        success: function( data, textStatus, jQxhr ){
            $("#rdfaCode").text(data);
            //document.getElementById('rdfa').innerHTML = data;     
        },
        error: function( jqXhr, textStatus, errorThrown ){
            document.getElementById('rdfaCode').innerHTML = errorThrown;
        }
    });
}

//Convert JSON-LD to Microdata
function jsonldToMicrodata(jsonld) {
    jsonldString = JSON.stringify(jsonld);
    postString = "content=" + jsonldString;

    $.ajax({
        url: 'http://rdf-translator.appspot.com/convert/json-ld/microdata/content',
        type: 'post',
        data: postString,
        success: function( data, textStatus, jQxhr ){
            $("#microdataCode").text(data);
            //document.getElementById('microdata').innerHTML = data;
        },
        error: function( jqXhr, textStatus, errorThrown ){
            document.getElementById('microdataCode').innerHTML = errorThrown;
        }
    });
}

//Display Example JSON-LD in a Modal
function displayModal(propertyName,example){
    var modalTitle = "Property &lt&lt" + propertyName+ "&gt&gt Example"
    var exampleDisplay = "<pre>" + example + "</pre>";
    bootbox.dialog({
        title: modalTitle ,
        message: exampleDisplay,
        size:"large"
    });
}

//Copy 
function copyToClipboard(){
    var activeTab = $('.tab-pane.active').find("code").text();
    
    console.log(activeTab);
    var range = document.createRange();
             range.selectNode(activeTab);
             window.getSelection().removeAllRanges();
             window.getSelection().addRange(range);
             document.execCommand("copy")
}

function downloadTest(){
    var activeTabContent = $('.tab-pane.active').find("code").text();
    var profileName =  $("#profileDropDown option:selected").text();
    var tabName = $('.nav-link.active').text();
    download(activeTabContent, profileName+"-"+tabName+".html", "text/html");
    console.log("test");
    console.log(activeTabContent);
}
