(function(){
  var STAR_SETS = ["✦", "★", "✧", "✶", "✺", "✸" ];
  var COLORS = [
    "#4e3565", // dark purple
    "#8a6cff",
    "#b892ff",
    "#ffb3d1",
    "#b4aabc",
    "#6a5acd"
  ];
  function randomInt(min, max){ return Math.floor(Math.random()*(max-min+1))+min; }
  function randomItem(arr){ return arr[Math.floor(Math.random()*arr.length)]; }
  function randomStarsColored(){
    var count = randomInt(1,4); // ensure at least one star
    var out = '';
    for (var i=0;i<count;i++){
      var star = randomItem(STAR_SETS);
      var color = randomItem(COLORS);
      out += '<span style="color:'+color+'">'+star+'</span>';
    }
    return out;
  }
  function wrapElement(el){
    if (!el || el.dataset.enhanced) return;
    var text = el.textContent;
    var frag = document.createDocumentFragment();
    for (var i=0;i<text.length;i++){
      var ch = text[i];
      var span = document.createElement('span');
      span.className = 'char';
      span.dataset.letter = ch;
      span.innerHTML = ch === ' ' ? '&nbsp;' : ch;
      span.addEventListener('mouseenter', function(ev){
        var node = ev.currentTarget;
        if (node.dataset.letter === ' ') return;
        node.innerHTML = randomStarsColored();
      });
      span.addEventListener('mouseleave', function(ev){
        var node = ev.currentTarget;
        node.innerHTML = node.dataset.letter === ' ' ? '&nbsp;' : node.dataset.letter;
      });
      frag.appendChild(span);
    }
    el.textContent = '';
    el.appendChild(frag);
    el.dataset.enhanced = 'true';
  }
  function init(){
    var taglines = document.querySelectorAll('.section-tag .tagline');
    var headings = document.querySelectorAll('.section-heading');
    var hero = document.querySelector('#top .title');
    for (var i=0;i<taglines.length;i++) wrapElement(taglines[i]);
    for (var j=0;j<headings.length;j++) wrapElement(headings[j]);
    if (hero) wrapElement(hero); // apply to hero title as requested, font preserved via CSS inherit
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
