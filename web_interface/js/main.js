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
  
  