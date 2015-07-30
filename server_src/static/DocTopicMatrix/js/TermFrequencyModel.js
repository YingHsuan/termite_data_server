/*
	TermFrequencyModel.js
		This model processes and packages data for the term frequency view.

	Initialization:
		Load term frequency from 'data/global-term-freqs.json'
	
	Data Update:
		Listens to FilteredTermTopicProbabilityModel (events: )

	Details:
	--------
	Pulls data from FilteredTermTopicProbilityModel. The model loads some parameters from 
	the url. On updates, the model receives a list
	of terms and generates a list of item(term, frequency) (same order as the term list
	received as input).  
*/
var TermFrequencyModel = Backbone.Model.extend({
	defaults : {
		"docIndex" : null,
		"docTerm": null,
		"totalTermFreqs": {},
		"topicalFreqMatrix": [],
		"selectedTopics": {} 
	}
});

TermFrequencyModel.prototype.initialize = function(options) {
	if (options.hasOwnProperty("url")) {
		this.url = options.url;
	}
	this.parentModel = null;
	this.stateModel = null;
	
	// original data
	this.originalMatrix = null;
	this.originalTopicIndex = null;
	this.originalTermIndex = null;
	this.originalTerm1 = null;
	
	// mappings
	this.topicMapping = null;
	this.termFreqMap = null;
}

/**
 * Initialize Term Frequency Model's parent and state model
 *
 * @private
 */
TermFrequencyModel.prototype.initModels = function( parent, state ){
	this.parentModel = parent;
	this.stateModel = state;
};

/**
 * Loads matrix, termIndex, topicIndex, and term to frequency mapping from the model's "url"
 * and triggers a loaded event that the next model (child model) listens to. Also, pulls 
 * any selected topics from state model and processes them.
 * (This function is called after the filtered model loaded event is fired)
 *
 * @param { string } the location of datafile to load values from
 * @return { void }
 */
TermFrequencyModel.prototype.load = function(){	

	var successHandler = function(model, response, options) {
		console.log("Loaded TermFrequencyModel 0703", model, response, options);
		
		this.set("docIndex", this.parentModel.get("docIndex"));
		//this.set("docTerm", this.parentModel.get("docTerm"));
		
		// UPDATE: many of these should come from stateModel instead of param file?
		this.originalMatrix = response.matrix;
		this.originalTopicIndex = response.topicIndex;
		this.originalTermIndex = response.docIndex;
		this.originalTerm1 = response.docTerm;
		this.topicMapping = response.topicMapping;
		
		this.termFreqMap = response.docFreqMap;
		this.getTotalTermFreqs();	
		
		// ask view to color selected topics
		var selected = _.groupBy(this.stateModel.get("topicIndex"), "selected")['true'];
		if( selected !== undefined ){
			this.update();
		}
		
		// signal completion
		this.trigger("loaded:freqModel");
	}.bind(this);
	var errorHandler = function(model, response, options) {
		console.log("Cannot load TermFrequencyModel 0703", model, response, options);
	}.bind(this);
	this.fetch({
		add : false,
		success : successHandler,
		error : errorHandler
	});	
};

/**
 * Calls appropriate functions to update based on data change(s)
 */
TermFrequencyModel.prototype.update = function(){
	this.set("docIndex", this.parentModel.get("docIndex"));
	this.set("docTerm", this.parentModel.get("docTerm"));
	this.generateTopicalMatrix( false );
	this.trigger("updated:TFM");
};

/** 
 * Finds total frequency for each term in termIndex
 *
 * @private
 */
TermFrequencyModel.prototype.getTotalTermFreqs = function(){
	var frequencies = {};
	var terms = this.parentModel.get("docIndex");
	for( var i = 0; i < terms.length; i++){
		frequencies[terms[i]] = this.termFreqMap[terms[i]];
	}
	this.set("totalTermFreqs", frequencies);
};

/** 
 * Finds frequency / topic for each term in termIndex and each topic in selectedTopics
 *
 * @private
 */
TermFrequencyModel.prototype.generateTopicalMatrix = function( keepQuiet ) {
	var frequencies = [];
	var terms = this.parentModel.get("docIndex");
	var selected = _.groupBy(this.stateModel.get("topicIndex"), "selected")['true'];
	if( selected !== undefined ){
		for( var index = 0; index < selected.length; index++){
			var tempList = [];
			var topic = selected[index].id;
			for( var i = 0; i < terms.length; i++){
				var termIndex = this.originalTermIndex.indexOf(terms[i]);
				tempList.push(this.originalMatrix[termIndex][topic]);
			}
			frequencies.push(tempList);
		}
	} else {
		//console.log("TFM: there are no selected topics");
	}
	this.getTotalTermFreqs();
	this.set("topicalFreqMatrix", frequencies, {silent: keepQuiet});
	return frequencies;
};

/** 
 * Called by term frequency view. Returns frequency / topic for every term in termIndex
 *
 * @this { TermFrequencyModel }
 * @param { int } target topic index
 * @return { array } list of topical frequencies in termIndex ordering
 */
TermFrequencyModel.prototype.getTopicalsForTopic = function( topic ) {
	var frequencies = [];
	var terms = this.get("docIndex");
	for( var i = 0; i < terms.length; i++){
		//var termIndex = this.originalTermIndex.indexOf(terms[i]);
		//frequencies.push(this.originalMatrix[termIndex][topic]);
	}
	return frequencies;
};