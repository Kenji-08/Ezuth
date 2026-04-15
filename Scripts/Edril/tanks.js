let nation = "Edril"

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('tank-list');
  if (!container) return;

  // Skeleton helpers to reduce perceived layout shift while fetching
  const skeletonWrapper = document.createElement('div');
  skeletonWrapper.className = 'tank-skeletons';
  const showSkeletons = (count = 3) => {
    skeletonWrapper.innerHTML = '';
    for (let i = 0; i < count; i++) {
      const sk = document.createElement('div');
      sk.className = 'tank-card skeleton-card';
      sk.style.minHeight = '140px';
      sk.style.background = '#efefef';
      sk.style.borderRadius = '4px';
      sk.style.marginBottom = '12px';
      skeletonWrapper.appendChild(sk);
    }
    container.appendChild(skeletonWrapper);
  };
  const removeSkeletons = () => {
    if (skeletonWrapper.parentNode) skeletonWrapper.parentNode.removeChild(skeletonWrapper);
  };

  // show skeletons immediately
  showSkeletons(3);

  fetch(`../Scripts/${nation}/tanks.json`)
    .then(response => {
      if (!response.ok) throw new Error('Failed to load tanks.json');
      return response.json();
    })
    .then(tanks => {
      removeSkeletons();
      if (!Array.isArray(tanks)) throw new Error('Invalid tanks data');
      const fragment = document.createDocumentFragment();
      tanks.forEach(tank => {
        const card = document.createElement('div');
        card.className = 'tank-card';

        const title = document.createElement('h2');
        title.textContent = tank.name || 'Unknown';
        card.appendChild(title);

        // use the `nation` variable for the flag path instead of JSON
        {
          const flag = document.createElement('img');
          flag.src = `../Images/flags/${nation}Small.jpg`;
          flag.alt = `${tank.name} flag`;
          flag.className = 'tank-flag';
          card.appendChild(flag);
        }

        const desig = document.createElement('p');
        desig.className = 'tank-designation';
        desig.textContent = tank.designation || '';
        card.appendChild(desig);

        if (tank.image) {
          const img = document.createElement('img');
          img.className = 'tank-image';
          img.src = tank.image;
          img.alt = tank.name || 'tank image';
          card.appendChild(img);
        }

        if (Array.isArray(tank.armaments) && tank.armaments.length) {
          const h = document.createElement('p');
          h.className = 'armaments-title';
          h.textContent = 'Armaments';
          card.appendChild(h);

          const ol = document.createElement('ol');
          tank.armaments.forEach(a => {
            const li = document.createElement('li');
            const cleaned = String(a).replace(/\bUnnamed\b\s*/gi, '').trim();
            li.textContent = cleaned;
            ol.appendChild(li);
          });
          card.appendChild(ol);
        }

        const stats = document.createElement('ul');
        stats.className = 'tank-stats';
        const addStat = (k, v) => {
          if (v === undefined || v === null) return;
          const s = String(v).trim();
          if (s === '' || s.toLowerCase() === 'null' || s.toLowerCase() === 'none') return;
          const li = document.createElement('li');
          li.textContent = `${k}: ${s}`;
          stats.appendChild(li);
        };

        // core stats (map to new JSON keys)
        addStat('Turret Rotation', tank.rotation);
        addStat('Vertical Guidance', tank.vertical);
        addStat('Reloading Rate', tank.reload);
        addStat('Crew', tank.crew);
        addStat('Mass', tank.mass);
        addStat('HP', tank.hp);
        addStat('Penetration', tank.penetration);
        addStat('Max Speed', tank.maxSpeed);
        addStat('Engine', tank.engine);
        addStat('Era', tank.era);
        card.appendChild(stats);

        fragment.appendChild(card);
      });
      // Append all cards at once to reduce layout shifts
      container.appendChild(fragment);
    })
    .catch(err => {
      removeSkeletons();
      console.error(err);
      container.textContent = 'Could not load tank data.';
    });
});
