const api = {
  ingest: () => fetch('/api/ingest', { method: 'POST' }).then(r => r.json()),
  recommend: (profile) => fetch('/api/recommend', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ profile }) }).then(r => r.json()),
  ask: (question, profile) => fetch('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, profile }) }).then(r => r.json()),
  mindmap: (source) => fetch(`/api/mindmap?source=${encodeURIComponent(source)}`).then(r => r.json()),
  feedback: (event, payload) => fetch('/api/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ event, payload }) }).then(r => r.json()),
};

const el = (id) => document.getElementById(id);

function getProfile() {
  return {
    branch: el('branch').value.trim(),
    interests: el('interests').value.split(',').map(s => s.trim()).filter(Boolean),
    skills: el('skills').value.split(',').map(s => s.trim()).filter(Boolean),
    goal: el('goal').value.trim(),
  };
}

function setStatus(msg) {
  el('status').textContent = msg || '';
}

async function drawMindmap(data) {
    const container = el('mindmap');
    const width = container.clientWidth;
    const height = 600;

    // Clear any existing SVG
    container.innerHTML = '';

    // Defensive: normalize response shape and ensure arrays exist
    if (!data || typeof data !== 'object') {
      container.innerHTML = '<div class="p-4 text-sm text-slate-600">No mindmap data available.</div>';
      return;
    }

    // Some backends return nested wrappers: { ok: true, graph: { nodes:..., links:... } }
    if (data.graph) data = data.graph;

    data.nodes = Array.isArray(data.nodes) ? data.nodes : [];
    data.links = Array.isArray(data.links) ? data.links : [];

    // Ensure each node has an `id` (fallback to label)
    data.nodes = data.nodes.map(n => ({ ...n, id: n.id || n.label || String(Math.random()).slice(2) }));

    const svg = d3.select('#mindmap')
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-500))
        .force("center", d3.forceCenter(width / 2, height / 2));

    // Create links
    const link = svg.append("g")
        .selectAll("line")
        .data(data.links)
        .enter()
        .append("line")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .attr("stroke-width", 2);

    // Create nodes
    const node = svg.append("g")
        .selectAll("g")
        .data(data.nodes)
        .enter()
        .append("g")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    // Add circles to nodes
    node.append("circle")
        .attr("r", d => d.group === 1 ? 25 : d.group === 2 ? 20 : 15)
        .attr("fill", d => {
            if (d.group === 1) return "#ff7f0e";
            if (d.group === 2) return "#1f77b4";
            return "#2ca02c";
        });

    // Add labels to nodes (use label if present, center with dy)
    node.append("text")
      .text(d => d.label || d.id)
  // Add labels to nodes (use label if present), center and wrap long text
      .attr("dy", d => d.group === 1 ? ".9em" : d.group === 2 ? ".8em" : ".7em")
    .attr("x", 0)
    .attr("text-anchor", "middle")
    .attr("fill", "#333")
    .style("font-size", d => d.group === 1 ? "14px" : "12px")
    .style("font-weight", d => d.group === 1 ? "bold" : "normal")
    .style("pointer-events", "none");

  label.each(function(d) {
    const txt = (d.label || d.id || '').toString();
    const words = txt.split(/\s+/);
    const lineLimit = 12; // approx chars per line
    let line = [];
    let lineNumber = 0;
    const y = 0;
    for (let i = 0; i < words.length; i++) {
    line.push(words[i]);
    const tspan = d3.select(this).append('tspan')
      .text(line.join(' '))
      .attr('x', 0)
      .attr('dy', lineNumber === 0 ? '0.35em' : '1.0em');
    if (tspan.node().getComputedTextLength() > (width / 6) && line.length > 1) {
      // remove last word and create new tspan
      line.pop();
      d3.select(this).selectAll('tspan').nodes().slice(-1)[0].textContent = line.join(' ');
      line = [words[i]];
      lineNumber += 1;
    }
    }
  });
      .attr("fill", "#333")
      .style("font-size", d => d.group === 1 ? "14px" : "12px")
      .style("font-weight", d => d.group === 1 ? "bold" : "normal")
      .style("pointer-events", "none");

    // Update force simulation on tick
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("transform", d => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

function renderRoadmap(plan) {
  const roadmap = el('roadmap');
  roadmap.innerHTML = '';
  if (!plan || !Array.isArray(plan.roadmap)) return;
  plan.roadmap.forEach(phase => {
    const div = document.createElement('div');
    div.className = 'border rounded-lg p-4';
    div.innerHTML = `<h4 class="font-semibold">${phase.title || 'Phase'}</h4>` +
                    `<ul class="list-disc pl-5 mt-2">${(phase.steps||[]).map(s => `<li>${s}</li>`).join('')}</ul>`;
    roadmap.appendChild(div);
  });

  const resources = el('resources');
  resources.innerHTML = (plan.resources||[]).map(r => `<li>${r.title}${r.url ? ` - <a class="text-indigo-600" href="${r.url}" target="_blank" rel="noreferrer">link</a>`: ''}</li>`).join('');
  const projects = el('projects');
  projects.innerHTML = (plan.projects||[]).map(p => `<li>${p}</li>`).join('');
}

function renderSources(sources) {
  const wrap = el('sources');
  wrap.innerHTML = '';
  (sources||[]).forEach(s => {
    const tag = document.createElement('span');
    tag.className = 'chip px-2 py-1 rounded-md text-sm';
    tag.textContent = `${s.title || s.source} (${s.section})`;
    tag.addEventListener('click', async () => {
      const g = await api.mindmap(s.source);
      if (g.ok) {
        let graph = g.graph;
        // Some deployments may double-wrap the response (e.g. { ok:true, graph: { ok:true, graph: {...} } })
        if (graph && graph.graph) graph = graph.graph;
        drawMindmap(graph);
      }
    });
    wrap.appendChild(tag);
  });
}

el('btnIngest').addEventListener('click', async () => {
  setStatus('Building index...');
  try {
    const res = await api.ingest();
    setStatus(res.ok ? `Indexed ${res.chunks_indexed} chunks.` : 'Ingestion failed');
  } catch (e) {
    console.error(e); setStatus('Ingestion error');
  }
});

el('btnRecommend').addEventListener('click', async () => {
  setStatus('Retrieving and generating roadmap...');
  const profile = getProfile();
  try {
    const res = await api.recommend(profile);
    if (res.ok) {
      renderRoadmap(res.plan);
      renderSources(res.sources);
      // feedback binding for roadmap
      el('roadmap').dataset.sources = JSON.stringify(res.sources||[]);
      el('roadmap').dataset.profile = JSON.stringify(profile);
      const top = res.sources && res.sources[0];
      if (top) {
        const g = await api.mindmap(top.source);
        if (g.ok) {
          let graph = g.graph;
          if (graph && graph.graph) graph = graph.graph;
          drawMindmap(graph);
        }
      }
      setStatus('');
    } else setStatus('Recommend failed');
  } catch (e) {
    console.error(e); setStatus('Recommend error');
  }
});

el('btnAsk').addEventListener('click', async () => {
  const q = el('question').value.trim();
  if (!q) return;
  setStatus('Retrieving and answering...');
  try {
    const res = await api.ask(q, getProfile());
    if (res.ok) {
      el('answer').textContent = res.answer;
      renderSources(res.sources);
      el('answer').dataset.sources = JSON.stringify(res.sources||[]);
      el('answer').dataset.question = q;
      setStatus('');
    } else setStatus('Ask failed');
  } catch (e) {
    console.error(e); setStatus('Ask error');
  }
});

// Feedback handlers
document.addEventListener('click', async (e) => {
  if (e.target.id === 'fb-answer-good' || e.target.id === 'fb-answer-bad') {
    const good = e.target.id === 'fb-answer-good';
    const sources = JSON.parse(el('answer').dataset.sources || '[]');
    const question = el('answer').dataset.question || '';
    await api.feedback('answer_feedback', { good, question, sources });
  }
});


