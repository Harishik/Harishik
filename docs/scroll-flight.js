(() => {
  const background = document.querySelector("#space");
  const trail = document.querySelector("#flight");
  const starsCtx = background.getContext("2d");
  const flightCtx = trail.getContext("2d");
  const main = document.querySelector("main");
  const page = document.querySelector(".page");
  const mot = document.querySelector("#motion");
  const tau = Math.PI * 2;

  const colors = {
    o:"#0d172c", n:"#23375c", b:"#597faa", r:"#c8394c",
    v:"#ff7463", l:"#fff3df", a:"#cf812c", g:"#ffd47b", e:"#7be1ff"
  };
  const webFrames = [
    [
      "............",
      "....oooo....",
      "...orvvro...",
      "...orllro...",
      "...orvvro...",
      ".ooonrno....",
      "orvronnno...",
      ".oonrvnno...",
      "...onrnro...",
      "...oobnoo...",
      "..obboo.....",
      "..oboo......",
      "..orro......",
      "...oo......."
    ],
    [
      "............",
      "....oooo....",
      "...orvvro...",
      "...orllro...",
      "...orvvro...",
      ".ooonrno....",
      "orvronnno...",
      ".oonrvnno...",
      "...onrnro...",
      "....obnoo...",
      "....obboo...",
      ".....onoo...",
      "......orro..",
      ".......oo..."
    ]
  ];
  const jetFrames = [
    [
      ".....oooo.....",
      "....orggro....",
      "....ogeeoo....",
      "....orggro....",
      "...oaarraao...",
      "..orgaegagro..",
      "..ogarragaro..",
      "...oarraro...",
      "...orgaagro...",
      "...oraaaaro...",
      "....or.or.....",
      "....oo.oo.....",
      ".............."
    ],
    [
      ".....oooo.....",
      "....orggro....",
      "....ogeeoo....",
      "....orggro....",
      "...oaarraao...",
      "..orgaegagro..",
      ".oagarragaro..",
      ".ooarrarooo...",
      "...orgaagro...",
      "...oraaaaro...",
      "....or.or.....",
      "....oo.oo.....",
      ".............."
    ]
  ];
  function bitmap(frames) {
    return frames.map(rows => {
      const sheet = document.createElement("canvas");
      sheet.width = Math.max(...rows.map(row => row.length));
      sheet.height = rows.length;
      const px = sheet.getContext("2d");
      rows.forEach((row,y) => [...row].forEach((cell,x) => {
        if (colors[cell]) {
          px.fillStyle = colors[cell];
          px.fillRect(x,y,1,1);
        }
      }));
      return sheet;
    });
  }
  const web = bitmap(webFrames);
  const jet = bitmap(jetFrames);

  let seed = 19547;
  function random() {
    seed = (1664525 * seed + 1013904223) >>> 0;
    return seed / 4294967296;
  }
  const stars = Array.from({length:220},() => ({
    x:random(),y:random(),depth:.2+random()*.82,
    phase:random()*tau,color:random()>.89 ? "#ffc590" : "#a5d9ff",
    width:.5+random()*1.25
  }));

  let w=1,h=1,pxRatio=1;
  let lastY=scrollY;
  let impulse=0;
  let direction="";
  let frame=0,lastTime=0,t=0;
  let enabled=false;
  let shellWidth=0;
  let edge=0;
  const reveal = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      const heading = entry.target.querySelector("h2:not(.sr)");
      if (enabled && heading) {
        heading.animate(
          [{opacity:.62,transform:"translateY(12px)"},{opacity:1,transform:"translateY(0)"}],
          {duration:280,easing:"cubic-bezier(0.23,1,0.32,1)"}
        );
      }
      reveal.unobserve(entry.target);
    }
  },{threshold:.07});
  main.querySelectorAll("section").forEach(section=>reveal.observe(section));

  function orbit(cx,cy,rx,ry,tilt,color,angle) {
    starsCtx.save();
    starsCtx.translate(cx,cy);
    starsCtx.rotate(tilt);
    starsCtx.strokeStyle=color;
    starsCtx.setLineDash([3,8]);
    starsCtx.beginPath();
    starsCtx.ellipse(0,0,rx,ry,0,0,tau);
    starsCtx.stroke();
    starsCtx.setLineDash([]);
    starsCtx.fillStyle="#e49e76";
    starsCtx.shadowBlur=13;
    starsCtx.shadowColor="#df7d51";
    starsCtx.beginPath();
    starsCtx.arc(rx*Math.cos(angle),ry*Math.sin(angle),2.4,0,tau);
    starsCtx.fill();
    starsCtx.restore();
  }
  function paintSpace() {
    starsCtx.clearRect(0,0,w,h);
    const p=enabled ? scrollY : 0;
    for (const s of stars) {
      const x=((s.x*w - t*(.002+s.depth*.011))%w+w)%w;
      const y=((s.y*h - p*s.depth*.13 + Math.sin(t*.00035+s.phase)*8)%h+h)%h;
      starsCtx.globalAlpha=.32+s.depth*.49+.12*Math.sin(t*.002+s.phase);
      starsCtx.fillStyle=s.color;
      starsCtx.fillRect(x,y,s.width,s.width);
      if (s.width>1.66) {
        starsCtx.globalAlpha*=.36;
        starsCtx.fillRect(x-3,y+.5,7,1);
        starsCtx.fillRect(x+.5,y-2,1,6);
      }
    }
    starsCtx.globalAlpha=1;
    const moonX=Math.min(w*.23,260)+Math.sin(t*.00019)*28;
    const moonY=h*.68-((p*.10)%(h*.25));
    const radius=Math.min(w*.27,335);
    const glow=starsCtx.createRadialGradient(moonX,moonY,radius*.74,moonX,moonY,radius*1.18);
    glow.addColorStop(0,"#060e1c20");
    glow.addColorStop(.54,"#172e4ccc");
    glow.addColorStop(.59,"#71adce88");
    glow.addColorStop(.67,"#366a983e");
    glow.addColorStop(1,"#23447300");
    starsCtx.fillStyle=glow;
    starsCtx.fillRect(moonX-radius*1.2,moonY-radius*1.2,radius*2.4,radius*2.4);
    starsCtx.globalAlpha=.65;
    orbit(w*.86,h*.29,Math.max(110,w*.18),51,-.43,"#cb7c6d68",t*.00032);
    orbit(w*.89,h*.68,Math.max(145,w*.21),69,.45,"#6eace579",-t*.00029+1.3);
    orbit(w*.21,h*.72,Math.min(w*.30,375),78,-.32,"#8fbbea61",t*.00025+2.1);
    starsCtx.globalAlpha=1;
  }

  function drawWeb(x,y,k) {
    const anchorX=Math.min(x-24,edge-5);
    const anchorY=16;
    const hookX=x-14;
    const hookY=y-12;
    flightCtx.strokeStyle="#d1effbcc";
    flightCtx.lineWidth=1.4;
    flightCtx.shadowColor="#8ad9ff";
    flightCtx.shadowBlur=7;
    flightCtx.beginPath();
    flightCtx.moveTo(anchorX,anchorY);
    flightCtx.quadraticCurveTo(anchorX+5*Math.sin(t*.016),hookY*.53,hookX,hookY);
    flightCtx.stroke();
    flightCtx.shadowBlur=0;
    for (let i=0;i<3;i++) {
      const cx=anchorX+((t/290+i/3)%1)*(hookX-anchorX);
      const cy=anchorY+((t/290+i/3)%1)*(hookY-anchorY);
      flightCtx.fillStyle="#e2f6ff";
      flightCtx.fillRect(cx-1,cy-1,2,2);
    }
    flightCtx.beginPath();
    flightCtx.arc(anchorX,anchorY,5+impulse*.09,0,tau);
    flightCtx.stroke();
    flightCtx.imageSmoothingEnabled=false;
    const sprite=web[Math.floor(t/125)%web.length];
    flightCtx.drawImage(sprite,Math.round(x-24*k),Math.round(y-24*k),sprite.width*3.4*k,sprite.height*3.4*k);
  }

  function drawJet(x,y,k) {
    const sprite=jet[Math.floor(t/108)%jet.length];
    const base=y+19*k;
    for (let i=1;i<=18;i++) {
      const spread=Math.sin(i*3.21+t*.017)*i*.65*k;
      flightCtx.globalAlpha=(1-i/20)*Math.min(1,impulse/7);
      flightCtx.fillStyle=i<5 ? "#fff4c3" : i%3 ? "#ff7851" : "#7be4ff";
      flightCtx.fillRect(Math.round(x+spread),Math.round(base+i*3*k),Math.max(1,5*k-i*.17),Math.max(2,8*k-i*.27));
    }
    flightCtx.globalAlpha=Math.min(1,impulse/3);
    flightCtx.imageSmoothingEnabled=false;
    flightCtx.drawImage(sprite,Math.round(x-24*k),Math.round(y-27*k),sprite.width*3.4*k,sprite.height*3.4*k);
  }

  function paintFlight() {
    flightCtx.clearRect(0,0,w,h);
    if (!enabled || impulse<.3) return;
    flightCtx.globalAlpha=Math.min(1,impulse/3);
    const mobile=shellWidth<680;
    const k=mobile ? .86 : 1.55;
    const x=mobile ? w-32 : Math.min(w-32,edge+36);
    const drift=direction==="tether" ? 1 : -1;
    const y=h*.59+Math.sin(t*.009)*12+drift*Math.min(impulse,22)*1.65;
    if(direction==="tether") drawWeb(x,y,k);
    else drawJet(x,y,k);
    flightCtx.globalAlpha=1;
  }

  function resize() {
    w=innerWidth; h=innerHeight;
    pxRatio=Math.min(1.6,devicePixelRatio||1);
    for (const [canvas,context] of [[background,starsCtx],[trail,flightCtx]]) {
      canvas.width=Math.round(w*pxRatio);
      canvas.height=Math.round(h*pxRatio);
      context.setTransform(pxRatio,0,0,pxRatio,0,0);
    }
    const rect=main.getBoundingClientRect();
    shellWidth=rect.width; edge=rect.right;
    paintSpace();
    paintFlight();
  }
  function render(now) {
    const delta=Math.min(45,Math.max(0,now-lastTime||16));
    lastTime=now;
    t+=delta;
    impulse*=Math.pow(.993,delta);
    paintSpace();
    paintFlight();
    if(impulse<.3) page.removeAttribute("data-flight");
    if(enabled) frame=requestAnimationFrame(render);
  }
  function setEffects() {
    const active=mot.textContent==="Pause motion";
    if (enabled===active) return;
    enabled=active;
    cancelAnimationFrame(frame);
    page.removeAttribute("data-flight");
    lastY=scrollY;
    impulse=0;
    lastTime=0;
    if(enabled) frame=requestAnimationFrame(render);
    else { t=0;paintSpace();paintFlight(); }
  }
  addEventListener("scroll",() => {
    const y=scrollY;
    const delta=y-lastY;
    lastY=y;
    if(!enabled||Math.abs(delta)<.5) return;
    direction=delta>0?"tether":"thruster";
    impulse=Math.min(32,Math.max(10,impulse+Math.abs(delta)*.46));
    page.dataset.flight=direction;
  },{passive:true});
  addEventListener("resize",resize,{passive:true});
  new MutationObserver(setEffects).observe(mot,{childList:true,characterData:true,subtree:true});
  resize();
  setEffects();
})();
