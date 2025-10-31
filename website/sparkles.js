(function(){
  var MAX_SPARKLES = 140;
  var LINGER_MS = 10;
  var SPARKLES_PER_MOVE = 2;
  var MIN_INTERVAL_MS = 12;
  var active = [];
  var lastTime = 0;

  function createSparkle(x, y){
    var el = document.createElement('span');
    el.className = 'sparkle';
    var size = 4 + Math.random()*7; // 4-11px
    el.style.width = size + 'px';
    el.style.height = size + 'px';
    var hue = 265 + Math.random()*40; // purple range
    el.style.background = 'radial-gradient(circle, rgba(255,255,255,0.95), hsla(' + hue + ',85%,72%,0.95) 60%, rgba(78,53,101,0) 70%)';
    var jx = Math.random()*10 - 5;
    var jy = Math.random()*10 - 5;
    el.style.left = (x + jx) + 'px';
    el.style.top = (y + jy) + 'px';
    document.body.appendChild(el);
    var life = LINGER_MS + Math.random()*300;
    setTimeout(function(){ if (el && el.parentNode) el.parentNode.removeChild(el); }, life);
    active.push(el);
    if (active.length > MAX_SPARKLES) {
      var old = active.shift();
      if (old && old.parentNode) old.parentNode.removeChild(old);
    }
  }

  window.addEventListener('mousemove', function(e){
    var now = performance.now();
    if (now - lastTime < MIN_INTERVAL_MS) return; // throttle
    lastTime = now;
    for (var i = 0; i < SPARKLES_PER_MOVE; i++) createSparkle(e.clientX, e.clientY);
  }, { passive: true });
})();
