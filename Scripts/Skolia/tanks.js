let nation = "Skolia"

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('tank-list');
  if (!container) return;

  fetch(`../Scripts/${nation}/tanks.json`)
    .then(response => {
      if (!response.ok) throw new Error('Failed to load tanks.json');
      return response.json();
    })
    .then(tanks => {
      if (!Array.isArray(tanks)) throw new Error('Invalid tanks data');
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
          card.appendChild(h);

          const ol = document.createElement('ol');
          tank.armaments.forEach(a => {
            const li = document.createElement('li');
            li.textContent = a;
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

        container.appendChild(card);
      });
    })
    .catch(err => {
      console.error(err);
      container.textContent = 'Could not load tank data.';
    });
});
