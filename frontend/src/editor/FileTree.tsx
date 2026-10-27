import { useMemo, useState } from "react";
import type { TreeFile } from "../api";

interface Props {
  files: TreeFile[];
  activePath: string | null;
  dirtyPaths: Set<string>;
  onOpen: (path: string) => void;
}

interface DirNode {
  name: string; // may be compacted, e.g. "backend/workspace/booking"
  key: string; // full path of the directory
  dirs: DirNode[];
  files: TreeFile[];
}

const baseName = (p: string) => p.split("/").pop() ?? p;

function buildTree(files: TreeFile[]): DirNode {
  const root: DirNode = { name: "", key: "", dirs: [], files: [] };
  for (const file of files) {
    const parts = file.path.split("/");
    let node = root;
    for (const part of parts.slice(0, -1)) {
      const key = node.key ? `${node.key}/${part}` : part;
      let next = node.dirs.find((d) => d.key === key);
      if (!next) {
        next = { name: part, key, dirs: [], files: [] };
        node.dirs.push(next);
      }
      node = next;
    }
    node.files.push(file);
  }
  // Compact chains of single-child folders, like VS Code's "compact folders".
  const compact = (node: DirNode): DirNode => {
    let current = node;
    while (current.files.length === 0 && current.dirs.length === 1 && current !== root) {
      const child = current.dirs[0];
      current = { ...child, name: `${current.name}/${child.name}` };
    }
    current.dirs = current.dirs.map(compact).sort((a, b) => a.name.localeCompare(b.name));
    current.files.sort((a, b) => baseName(a.path).localeCompare(baseName(b.path)));
    return current;
  };
  return compact(root);
}

const ICON: Record<string, string> = { py: "py", ts: "ts", tsx: "tsx", md: "md", toml: "⚙", json: "{}" };

function FileRow({ file, depth, active, dirty, label, onOpen }: {
  file: TreeFile;
  depth: number;
  active: boolean;
  dirty: boolean;
  label: string;
  onOpen: (path: string) => void;
}) {
  const ext = file.path.split(".").pop() ?? "";
  return (
    <button
      className={`tree-row file ${active ? "active" : ""}`}
      style={{ paddingLeft: 8 + depth * 12 }}
      title={file.path}
      onClick={() => onOpen(file.path)}
    >
      <span className={`file-icon ext-${ext}`}>{ICON[ext] ?? "·"}</span>
      <span className="tree-label">{label}</span>
      {file.read_only && <span className="tree-lock" title="Read-only">🔒</span>}
      {dirty && <span className="dirty-dot" aria-label="unsaved" />}
    </button>
  );
}

export function FileTree({ files, activePath, dirtyPaths, onOpen }: Props) {
  const [filter, setFilter] = useState("");
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const pinned = files.filter((f) => f.pinned);
  const tree = useMemo(() => buildTree(files.filter((f) => !f.pinned)), [files]);

  const toggle = (key: string) =>
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

  const renderDir = (node: DirNode, depth: number): React.ReactNode => (
    <div key={node.key || "root"}>
      {node.key && (
        <button className="tree-row dir" style={{ paddingLeft: 8 + depth * 12 }} onClick={() => toggle(node.key)}>
          <span className="tree-caret">{collapsed.has(node.key) ? "▸" : "▾"}</span>
          <span className="tree-label">{node.name}</span>
        </button>
      )}
      {!collapsed.has(node.key) && (
        <>
          {node.dirs.map((d) => renderDir(d, node.key ? depth + 1 : depth))}
          {node.files.map((f) => (
            <FileRow
              key={f.path}
              file={f}
              depth={node.key ? depth + 1 : depth}
              active={f.path === activePath}
              dirty={dirtyPaths.has(f.path)}
              label={baseName(f.path)}
              onOpen={onOpen}
            />
          ))}
        </>
      )}
    </div>
  );

  const query = filter.trim().toLowerCase();
  const matches = query ? files.filter((f) => f.path.toLowerCase().includes(query)) : [];

  return (
    <nav className="file-tree" aria-label="Files">
      <input
        className="tree-filter"
        placeholder="Filter files…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && matches[0]) onOpen(matches[0].path);
          if (e.key === "Escape") setFilter("");
        }}
      />
      <div className="tree-scroll">
        {query
          ? matches.map((f) => (
              <FileRow
                key={f.path}
                file={f}
                depth={0}
                active={f.path === activePath}
                dirty={dirtyPaths.has(f.path)}
                label={f.pinned ? baseName(f.path) : f.path.split("/").slice(-2).join("/")}
                onOpen={onOpen}
              />
            ))
          : (
            <>
              {pinned.map((f) => (
                <FileRow
                  key={f.path}
                  file={f}
                  depth={0}
                  active={f.path === activePath}
                  dirty={false}
                  label={baseName(f.path)}
                  onOpen={onOpen}
                />
              ))}
              {renderDir(tree, 0)}
            </>
          )}
        {query && matches.length === 0 && <p className="muted small pad-sm">No matching files</p>}
      </div>
    </nav>
  );
}
