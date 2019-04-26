!function(){
	function replaceBrackets(p1) {
  		var s1 = p1.replace('[', '')
  		var s2 = s1.replace(']', '')
  	return s2
	}

function performMark() {
  console.log("performMark")

  // Read the keyword
  var keyword = keywordInput.value;

  // Determine selected options
  var options = {};
  [].forEach.call(optionInputs, function(opt) {
    options[opt.value] = opt.checked;
  });

  // Remove previous marked elements and mark
  // the new keyword inside the context
  markInstance.unmark({
    done: function(){
      markInstance.mark(keyword, options);
    }
  });
}

}();
