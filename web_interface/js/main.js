(function(){
    if (window.IntersectionObserver) {
      initObserver();
      document.body.setAttribute('animate-on-scroll', true);
    }
  
    /**
     * Initializes an Intersection Observer that monitors if any elements
     * with the right class name come into view.
     **/
    function initObserver() {
      const observer = new IntersectionObserver(callback);
      const items = document.querySelectorAll('.content, .animate-on-scroll');
  
      for (let i = 0; i < items.length; i++) {
        observer.observe(items[i]);
      }
    }
  
    /**
     * Callback for the Intersection Observer when an item comes into view.
     * @param {Array?} entries The elements being monitored that have entered or
     * exited the viewport.
     **/
    function callback(entries) {
      for (let i in entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('in-view');
          }
          // Don't remove the class after we've added it, so that
          // we don't over animate.
        });
      }
    }
  })();

//- Using an anonymous function:
function getInput() {
    var parameters = new Object();
    parameters.batch_size = document.getElementById("batch_size").value;
    parameters.learning_rate = document.getElementById("lr").value;
    parameters.num_steps = document.getElementById("num_steps").value;
    parameters.steps_per_save = document.getElementById("steps_per_save").value;
    parameters.steps_per_summary = document.getElementById("steps_per_summary").value;
    parameters.early_stop_loss_value = document.getElementById("early_stop").value;
    var jsonString= JSON.stringify(parameters);
    window.alert(jsonString); 
};
