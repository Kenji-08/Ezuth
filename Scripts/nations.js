document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('nation-list');
  if (!container) return;

  fetch('../Scripts/nations.json')
    .then(res => {
      if (!res.ok) throw new Error('Failed to load nations.json');
      return res.json();
    })
    .then(nations => {
      if (!Array.isArray(nations)) throw new Error('Invalid nations data');
      nations.forEach(n => {
        const card = document.createElement('div');
        card.className = 'nation-card';

        const title = document.createElement('h2');
        title.textContent = n.name || 'Unknown';
        card.appendChild(title);

        if (n.flag) {
          const flag = document.createElement('img');
          flag.className = 'nation-flag';
          flag.src = n.flag;
          flag.alt = `${n.name} flag`;
          card.appendChild(flag);
        }

        if (n.description) {
          const p = document.createElement('p');
          p.textContent = n.description;
          card.appendChild(p);
        }

        const links = document.createElement('p');
        if (n.tanksPage) {
          const a = document.createElement('a');
          a.href = n.tanksPage;
          a.textContent = 'Tanks';
          links.appendChild(a);
        }
        if (n.more) {
          const b = document.createElement('a');
          b.href = n.more;
          b.textContent = 'More';
          b.style.marginLeft = '8px';
          links.appendChild(b);
        }
        card.appendChild(links);

        container.appendChild(card);
      });
    })
    .catch(err => {
      console.error(err);
      container.textContent = 'Could not load nations.';
    });
});
