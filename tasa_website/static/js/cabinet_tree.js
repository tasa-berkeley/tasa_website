/* Public /alumni page: a FEATURE-DRIVEN lineage engine.
 *
 * Members carry generic "features" (see helpers.cabinet_member_dict): `relations` (person->person
 * links), `attributes` (single values), and `sequences` (multi-valued, time-ordered lists). A small
 * DIMENSIONS registry describes each way to organize the graph; two generic builders turn a feature
 * into a Cytoscape graph:
 *   - relation: follow a person->person link (e.g. big -> little).
 *   - sequence: group members by a shared value, sort each group by an order key, and chain them
 *     (predecessor -> successor) — e.g. Position by semester, Major by grad year.
 * The "Organize by" selector rebuilds the graph from whichever feature is chosen. Adding a new
 * lineage is one DIMENSIONS entry + the matching data in the serialized member — no new graph code.
 *
 * Rendered with Cytoscape + the fcose layout. Loaded non-deferred (before the deferred Alpine) so the
 * component registers on alpine:init. `window.CABINET_DATA` is inlined by templates/alumni.html.
 */
document.addEventListener('alpine:init', () => {
  // Distinct, reasonably accessible hues for coloring the separate chains of a sequence feature.
  const PALETTE = ['#0284c7', '#ea580c', '#7c3aed', '#059669', '#db2777', '#ca8a04',
                   '#0891b2', '#dc2626', '#4f46e5', '#65a30d', '#c026d3', '#0d9488'];
  const RELATION_COLOR = '#0284c7';   // single color for a relation feature (big/little)

  // The organizing features. type 'relation' follows a link; type 'sequence' groups + sorts + chains.
  // `order` sorts members within a chain; `groupSortAttr`/`groupSortNumeric` order the groups themselves
  // (so e.g. intern classes read chronologically, class years numerically) — else groups sort by name.
  const DIMENSIONS = [
    { key: 'biglittle', label: 'Big / Little', type: 'relation', relation: 'big' },
    { key: 'position', label: 'Position', type: 'sequence', kind: 'multi',
      seqPath: ['sequences', 'position'], group: 'value', order: 'sortKey' },
    { key: 'internclass', label: 'Intern class', type: 'sequence', kind: 'single',
      attr: 'internClass', groupSortAttr: 'internClassOrd', order: 'name' },
    { key: 'major', label: 'Major', type: 'sequence', kind: 'single', attr: 'major', order: 'grad_year' },
    { key: 'majorfield', label: 'Major field', type: 'sequence', kind: 'single', attr: 'majorField', order: 'grad_year' },
    { key: 'classyear', label: 'Class year', type: 'sequence', kind: 'single', attr: 'classYear', groupSortNumeric: true, order: 'name' },
  ];

  // A soft accent "orb" with the member's initials, for members without a photo.
  const initialsImage = (initials) => {
    const svg =
      "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'>" +
      "<text x='50%' y='50%' dy='.35em' text-anchor='middle' font-family='DM Sans, sans-serif' " +
      "font-size='52' font-weight='700' fill='#075985'>" + initials + "</text></svg>";
    return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
  };

  Alpine.data('cabinetTree', (data) => ({
    members: Array.isArray(data) ? data : [],
    byId: {},
    childrenOf: {},          // big_id -> [member, ...]  (for the modal's Big/Littles)
    dimensions: DIMENSIONS.map((d) => ({ key: d.key, label: d.label })),
    dimension: 'biglittle',
    legend: [],
    filters: { name: '', gradYear: '' },
    selected: null,
    total: 0,
    count: 0,
    cy: null,

    init() {
      this.members.forEach((m) => { this.byId[m.id] = m; });
      this.members.forEach((m) => {
        if (m.big_id != null && this.byId[m.big_id]) {
          (this.childrenOf[m.big_id] = this.childrenOf[m.big_id] || []).push(m);
        }
      });
      this.$nextTick(() => this.render());
    },

    render() {
      const container = this.$refs.graph;
      if (!container || typeof cytoscape === 'undefined') return;
      if (window.cytoscapeDagre && !cytoscape.__dagreRegistered) {
        try { cytoscape.use(window.cytoscapeDagre); cytoscape.__dagreRegistered = true; } catch (e) { /* already */ }
      }
      this.layoutName = window.cytoscapeDagre ? 'dagre' : 'breadthfirst';

      this.cy = cytoscape({
        container,
        elements: [],
        minZoom: 0.2, maxZoom: 2.5, boxSelectionEnabled: false, pixelRatio: 'auto',
        style: [
          {
            selector: 'node',
            style: {
              width: 60, height: 60, shape: 'ellipse',
              'background-color': '#ffffff', 'background-fit': 'cover',
              'border-width': 3, 'border-color': '#0284c7', 'overlay-opacity': 0,
              label: 'data(label)', 'font-size': 12, 'font-weight': 700, color: '#171717',
              'min-zoomed-font-size': 9,
              'text-valign': 'bottom', 'text-halign': 'center', 'text-margin-y': 7,
              'text-wrap': 'wrap', 'text-max-width': 104,
              'text-background-color': '#ffffff', 'text-background-opacity': 0.88,
              'text-background-shape': 'roundrectangle', 'text-background-padding': 3,
              'transition-property': 'width height border-color border-width opacity background-color',
              'transition-duration': '180ms', 'transition-timing-function': 'ease-out',
            },
          },
          { selector: 'node.has-photo', style: { 'background-image': 'data(image)', 'background-fit': 'cover', 'border-color': '#0284c7' } },
          {
            selector: 'node.has-initials',
            style: {
              'background-color': '#e0f2fe', 'border-color': '#0369a1',
              'background-image': 'data(image)', 'background-fit': 'none',
              'background-width': '58%', 'background-height': '58%',
              'background-position-x': '50%', 'background-position-y': '50%',
            },
          },
          {
            selector: 'edge',
            style: {
              width: 3, 'line-color': 'data(color)', 'curve-style': 'bezier', opacity: 0.95,
              'target-arrow-shape': 'triangle', 'target-arrow-color': 'data(color)', 'arrow-scale': 0.9,
              'transition-property': 'width opacity', 'transition-duration': '180ms',
            },
          },
          { selector: 'node.hl-node', style: { 'border-color': '#0c4a6e', 'border-width': 5, width: 70, height: 70, 'z-index': 30 } },
          { selector: 'edge.hl-edge', style: { width: 5, opacity: 1, 'z-index': 30 } },
          { selector: 'node.match', style: { 'border-color': '#111827', 'border-width': 5, width: 68, height: 68 } },
          { selector: '.faded', style: { opacity: 0.1 } },
        ],
      });

      this.cy.on('mouseover', 'node', (e) => this.highlightLineage(e.target.data('mid')));
      this.cy.on('mouseout', 'node', () => this.clearHover());
      this.cy.on('tap', 'node', (e) => this.select(e.target.data('mid')));
      this.cy.on('tap', (e) => { if (e.target === this.cy) this.selected = null; });

      this.setDimension(this.dimension);
    },

    // ---- feature -> graph builders -------------------------------------
    nodeFor(m) {
      return {
        data: { id: String(m.id), mid: m.id, label: m.name, image: m.image || initialsImage(m.initials || '?') },
        classes: m.image ? 'has-photo' : 'has-initials',
      };
    },
    cmp(a, b) {   // numeric when both numbers, else string; nulls/blanks last
      const na = a == null || a === '', nb = b == null || b === '';
      if (na && nb) return 0;
      if (na) return 1;
      if (nb) return -1;
      if (typeof a === 'number' && typeof b === 'number') return a - b;
      return String(a).localeCompare(String(b), undefined, { numeric: true });
    },
    resolveOrder(m, field) {
      if (field === 'name') return m.name;
      if (m[field] !== undefined && m[field] !== null) return m[field];
      return m.attributes ? m.attributes[field] : undefined;
    },
    instancesFor(m, dim) {
      if (dim.kind === 'multi') {
        let arr = m;
        dim.seqPath.forEach((k) => { arr = arr ? arr[k] : undefined; });
        if (!Array.isArray(arr)) return [];
        return arr
          .map((it) => {
            const group = it[dim.group] == null ? '' : String(it[dim.group]);
            return { group, sortVal: it[dim.order], groupSort: group };
          })
          .filter((x) => x.group !== '');
      }
      const v = m.attributes ? m.attributes[dim.attr] : undefined;
      if (v == null || v === '') return [];
      let groupSort;
      if (dim.groupSortAttr) groupSort = m.attributes ? m.attributes[dim.groupSortAttr] : undefined;
      else if (dim.groupSortNumeric) groupSort = Number(v);
      else groupSort = String(v);
      return [{ group: String(v), sortVal: this.resolveOrder(m, dim.order), groupSort }];
    },
    buildElements(dim) {
      const nodesById = {};
      const edges = [];
      const legend = [];
      let ec = 0;
      const addNode = (m) => { if (m && !nodesById[m.id]) nodesById[m.id] = this.nodeFor(m); };

      if (dim.type === 'relation') {
        this.members.forEach((m) => addNode(m));   // relations show everyone (isolated nodes allowed)
        this.members.forEach((m) => {
          const targetId = m.relations && m.relations[dim.relation];
          if (targetId != null && this.byId[targetId]) {
            edges.push({ data: { id: 'e' + ec++, source: String(targetId), target: String(m.id), color: RELATION_COLOR } });
          }
        });
      } else {
        // group members by feature value; within each group, sort and chain (dedupe repeats per member)
        const groups = {};        // group -> Map(memberId -> min sortVal)
        const groupSort = {};     // group -> min groupSort key (orders the groups/legend)
        this.members.forEach((m) => {
          this.instancesFor(m, dim).forEach((inst) => {
            const g = groups[inst.group] || (groups[inst.group] = new Map());
            const prev = g.get(m.id);
            if (prev === undefined || this.cmp(inst.sortVal, prev) < 0) g.set(m.id, inst.sortVal);
            if (!(inst.group in groupSort) || this.cmp(inst.groupSort, groupSort[inst.group]) < 0) {
              groupSort[inst.group] = inst.groupSort;
            }
          });
        });
        const groupKeys = Object.keys(groups).sort(
          (a, b) => this.cmp(groupSort[a], groupSort[b]) || a.localeCompare(b));
        groupKeys.forEach((gk, gi) => {
          const color = PALETTE[gi % PALETTE.length];
          legend.push({ label: gk, color });
          const ordered = [...groups[gk].entries()].sort((a, b) => this.cmp(a[1], b[1]));
          ordered.forEach(([mid]) => addNode(this.byId[mid]));
          for (let i = 0; i < ordered.length - 1; i++) {
            edges.push({ data: { id: 'e' + ec++, source: String(ordered[i][0]), target: String(ordered[i + 1][0]), color, group: gk } });
          }
        });
      }
      return { nodes: Object.values(nodesById), edges, legend };
    },

    setDimension(key) {
      if (!this.cy) return;
      this.dimension = key;
      const dim = DIMENSIONS.find((d) => d.key === key) || DIMENSIONS[0];
      const { nodes, edges, legend } = this.buildElements(dim);
      this.legend = dim.type === 'sequence' ? legend : [];
      this.selected = null;
      this.cy.startBatch();
      this.cy.elements().remove();
      this.cy.add(nodes);
      this.cy.add(edges);
      this.cy.endBatch();
      this.total = this.cy.nodes().length;
      this.runLayout();
      this.applyFilter();
    },
    layoutOptions() {
      // Top-to-bottom layered layout: sources (bigs / oldest) on top, flowing down to
      // littles / newest. Edges are directed older -> newer, so ranks read chronologically.
      if (this.layoutName === 'dagre') {
        return {
          name: 'dagre', rankDir: 'TB', nodeSep: 42, rankSep: 92, edgeSep: 12, ranker: 'network-simplex',
          animate: true, animationDuration: 500, animationEasing: 'ease-out', fit: true, padding: 44,
        };
      }
      return { name: 'breadthfirst', directed: true, spacingFactor: 1.1, padding: 44, animate: true, animationDuration: 500 };
    },
    runLayout() {
      this.cy.layout(this.layoutOptions()).run();   // dagre/breadthfirst fit to the viewport themselves
    },

    // ---- hover: trace the connected lineage (works for any feature) -----
    highlightLineage(nodeId) {
      if (!this.cy) return;
      const node = this.cy.getElementById(String(nodeId));
      if (node.empty()) return;
      const keep = node.union(node.successors()).union(node.predecessors());
      this.cy.batch(() => {
        this.cy.elements().addClass('faded').removeClass('hl-node hl-edge');
        keep.nodes().removeClass('faded').addClass('hl-node');
        keep.edges().removeClass('faded').addClass('hl-edge');
      });
    },
    clearHover() {
      if (!this.cy) return;
      this.cy.elements().removeClass('faded hl-node hl-edge');
      if (this.filtered) this.applyFilter();
    },

    // ---- filtering (name / grad year), applied to the current view -----
    get filtered() {
      return !!(this.filters.name.trim() || this.filters.gradYear);
    },
    matches(m) {
      const n = this.filters.name.trim().toLowerCase();
      const gy = this.filters.gradYear;
      if (n && !(m.name || '').toLowerCase().includes(n)) return false;
      if (gy && String(m.grad_year == null ? '' : m.grad_year) !== String(gy)) return false;
      return true;
    },
    applyFilter() {
      if (!this.cy) return;
      this.cy.elements().removeClass('hl-node hl-edge');
      if (!this.filtered) {
        this.cy.elements().removeClass('faded match');
        this.count = this.cy.nodes().length;
        return;
      }
      const matched = new Set();
      this.cy.batch(() => {
        this.cy.nodes().forEach((n) => {
          const m = this.byId[n.data('mid')];
          const hit = !!(m && this.matches(m));
          n.toggleClass('match', hit);
          n.toggleClass('faded', !hit);
          if (hit) matched.add(n.id());
        });
        this.cy.edges().forEach((e) => {
          e.toggleClass('faded', !(matched.has(e.source().id()) && matched.has(e.target().id())));
        });
      });
      this.count = matched.size;
      const hits = this.cy.nodes('.match');
      if (hits.length) this.cy.animate({ fit: { eles: hits, padding: 70 }, duration: 350, easing: 'ease-out' });
    },
    resetFilters() {
      this.filters = { name: '', gradYear: '' };
      this.applyFilter();
      this.fitAll();
    },

    // ---- modal + navigation helpers -----------------------------------
    select(id) {
      this.selected = this.byId[id] || null;
      if (this.selected && this.cy) {
        const node = this.cy.getElementById(String(id));
        if (node && node.nonempty()) this.cy.animate({ center: { eles: node }, duration: 250, easing: 'ease-out' });
      }
    },
    subtitle(m) {
      const bits = [];
      if (m.role) bits.push(m.role);
      if (m.major) bits.push(m.major);
      if (m.grad_year) bits.push('Class of ' + m.grad_year);
      return bits.join(' · ');
    },
    positionsOf(m) {
      return (m && m.sequences && m.sequences.position) || [];
    },
    bigName(m) {
      return m && m.big_id != null && this.byId[m.big_id] ? this.byId[m.big_id].name : '';
    },
    littlesOf(m) {
      return m ? (this.childrenOf[m.id] || []) : [];
    },

    // ---- zoom controls ------------------------------------------------
    zoomBy(factor) {
      if (!this.cy) return;
      const z = Math.min(this.cy.maxZoom(), Math.max(this.cy.minZoom(), this.cy.zoom() * factor));
      this.cy.animate({ zoom: { level: z, renderedPosition: { x: this.cy.width() / 2, y: this.cy.height() / 2 } }, duration: 150 });
    },
    zoomIn() { this.zoomBy(1.3); },
    zoomOut() { this.zoomBy(0.77); },
    fitAll() { if (this.cy) this.cy.animate({ fit: { eles: this.cy.elements(), padding: 48 }, duration: 300, easing: 'ease-out' }); },
  }));
});
