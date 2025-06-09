#!/usr/bin/env python3
"""
N8N Workflow Debugger
Analyzes workflow structure and identifies potential execution flow issues
"""

import json
import requests
import time
from datetime import datetime, timedelta
import jwt
from typing import Dict, List, Set, Optional
from pathlib import Path

class N8NWorkflowDebugger:
    def __init__(self, workflow_file_path: str):
        """Initialize debugger with workflow JSON file"""
        with open(workflow_file_path, 'r', encoding='utf-8') as f:
            self.workflow = json.load(f)
        
        self.nodes = {node['id']: node for node in self.workflow['nodes']}
        self.connections = self.workflow.get('connections', {})
        
    def analyze_execution_flow(self) -> Dict:
        """Analyze workflow execution flow and identify potential issues"""
        print("🔍 Analyzing N8N Workflow Execution Flow")
        print("=" * 60)
        
        issues = []
        analysis = {
            'total_nodes': len(self.nodes),
            'execution_paths': [],
            'potential_issues': issues,
            'conditional_nodes': [],
            'expression_references': []
        }
        
        # Find conditional nodes
        for node_id, node in self.nodes.items():
            if node['type'] == 'n8n-nodes-base.if':
                analysis['conditional_nodes'].append({
                    'id': node_id,
                    'name': node['name'],
                    'conditions': node.get('parameters', {}).get('conditions', {})
                })
        
        # Find nodes with expressions that reference other nodes
        for node_id, node in self.nodes.items():
            expressions = self._find_node_references(node)
            if expressions:
                analysis['expression_references'].append({
                    'node_id': node_id,
                    'node_name': node['name'],
                    'references': expressions
                })
        
        # Check for unexecuted node references
        for ref_info in analysis['expression_references']:
            for ref in ref_info['references']:
                referenced_node_name = ref['referenced_node']
                if self._is_conditional_reference_risky(ref_info['node_name'], referenced_node_name):
                    issues.append({
                        'type': 'unexecuted_reference',
                        'severity': 'high',
                        'node': ref_info['node_name'],
                        'referenced_node': referenced_node_name,
                        'expression': ref['expression'],
                        'description': f"Node '{ref_info['node_name']}' references '{referenced_node_name}' which may not execute if conditions aren't met"
                    })
        
        return analysis
    
    def _find_node_references(self, node: Dict) -> List[Dict]:
        """Find all expressions that reference other nodes"""
        references = []
        
        def search_for_references(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    search_for_references(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_for_references(item, f"{path}[{i}]")
            elif isinstance(obj, str):
                # Look for node references like $('NodeName')
                import re
                pattern = r"\$\('([^']+)'\)"
                matches = re.findall(pattern, obj)
                for match in matches:
                    references.append({
                        'referenced_node': match,
                        'expression': obj,
                        'location': path
                    })
        
        search_for_references(node.get('parameters', {}))
        return references
    
    def _is_conditional_reference_risky(self, referencing_node: str, referenced_node: str) -> bool:
        """Check if a reference to a conditional node is risky"""
        # Find the referenced node
        referenced_node_obj = None
        for node in self.nodes.values():
            if node['name'] == referenced_node:
                referenced_node_obj = node
                break
        
        if not referenced_node_obj:
            return True  # Referenced node doesn't exist
        
        # If it's a conditional node (IF), it's risky
        if referenced_node_obj['type'] == 'n8n-nodes-base.if':
            return True
        
        return False
    
    def generate_execution_map(self) -> Dict:
        """Generate a map of workflow execution paths"""
        execution_map = {}
        
        # Find trigger nodes (no incoming connections)
        trigger_nodes = []
        all_target_nodes = set()
        
        for source_node, connections in self.connections.items():
            for connection_type, connection_list in connections.items():
                for connection_group in connection_list:
                    for connection in connection_group:
                        all_target_nodes.add(connection['node'])
        
        for node_id, node in self.nodes.items():
            if node['name'] not in all_target_nodes:
                trigger_nodes.append(node['name'])
        
        print(f"🚀 Trigger nodes: {trigger_nodes}")
        
        # Trace execution paths
        for trigger in trigger_nodes:
            execution_map[trigger] = self._trace_execution_path(trigger, set())
        
        return execution_map
    
    def _trace_execution_path(self, node_name: str, visited: Set[str]) -> List[str]:
        """Trace execution path from a given node"""
        if node_name in visited:
            return [f"{node_name} (circular)"]
        
        visited.add(node_name)
        path = [node_name]
        
        # Find connections from this node
        node_connections = self.connections.get(node_name, {})
        
        for connection_type, connection_list in node_connections.items():
            for connection_group in connection_list:
                for connection in connection_group:
                    target_node = connection['node']
                    sub_path = self._trace_execution_path(target_node, visited.copy())
                    path.extend(sub_path)
        
        return path
    
    def suggest_fixes(self, analysis: Dict) -> List[str]:
        """Suggest fixes for identified issues"""
        suggestions = []
        
        for issue in analysis['potential_issues']:
            if issue['type'] == 'unexecuted_reference':
                suggestions.append(
                    f"Fix for '{issue['node']}' referencing '{issue['referenced_node']}':\n"
                    f"  - Use safe reference: $('{ issue['referenced_node']}').first() ? $('{ issue['referenced_node']}').all().length : 0\n"
                    f"  - Or restructure workflow to ensure execution order\n"
                    f"  - Or remove reference to conditional node from final response"
                )
        
        return suggestions
    
    def test_workflow_with_backend(self) -> Dict:
        """Test workflow execution with backend API"""
        print("\n🧪 Testing Workflow with Backend API")
        print("-" * 40)
        
        # Generate token
        token = self._generate_token()
        
        # Test webhook
        webhook_url = "http://localhost:5678/webhook/lead-activity"
        test_data = {
            "test": True,
            "trigger": "debugger_test",
            "timestamp": time.time()
        }
        
        try:
            response = requests.post(webhook_url, json=test_data, timeout=30)
            return {
                'status': response.status_code,
                'success': response.status_code == 200,
                'response': response.text[:500] if response.text else "Empty response",
                'error': None
            }
        except Exception as e:
            return {
                'status': None,
                'success': False,
                'response': None,
                'error': str(e)
            }
    
    def _generate_token(self, username="devuser", expires_minutes=30):
        """Generate JWT token for testing"""
        payload = {
            "sub": username,
            "exp": int((datetime.now() + timedelta(minutes=expires_minutes)).timestamp())
        }
        secret_key = "your-secret-key-here-change-this-in-production"
        return jwt.encode(payload, secret_key, algorithm="HS256")
    
    def run_full_analysis(self):
        """Run complete workflow analysis and debugging"""
        print("🔧 N8N Workflow Debugger - Full Analysis")
        print("=" * 60)
        
        # Analyze execution flow
        analysis = self.analyze_execution_flow()
        
        print(f"\n📊 Workflow Overview:")
        print(f"   Total nodes: {analysis['total_nodes']}")
        print(f"   Conditional nodes: {len(analysis['conditional_nodes'])}")
        print(f"   Nodes with references: {len(analysis['expression_references'])}")
        print(f"   Issues found: {len(analysis['potential_issues'])}")
        
        # Show conditional nodes
        if analysis['conditional_nodes']:
            print(f"\n🔀 Conditional Nodes:")
            for cnode in analysis['conditional_nodes']:
                print(f"   - {cnode['name']} (ID: {cnode['id']})")
        
        # Show issues
        if analysis['potential_issues']:
            print(f"\n⚠️  Issues Found:")
            for i, issue in enumerate(analysis['potential_issues'], 1):
                print(f"   {i}. {issue['description']}")
                print(f"      Severity: {issue['severity']}")
                print(f"      Expression: {issue['expression']}")
        
        # Show fixes
        suggestions = self.suggest_fixes(analysis)
        if suggestions:
            print(f"\n🔧 Suggested Fixes:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion}")
        
        # Generate execution map
        execution_map = self.generate_execution_map()
        print(f"\n🗺️  Execution Paths:")
        for trigger, path in execution_map.items():
            print(f"   {trigger} → {' → '.join(path)}")
        
        # Test with backend
        test_result = self.test_workflow_with_backend()
        print(f"\n🧪 Backend Test Result:")
        print(f"   Status: {'✅ PASS' if test_result['success'] else '❌ FAIL'}")
        if not test_result['success']:
            print(f"   Error: {test_result['error']}")
        
        return analysis

def analyze_workflow():
    # Path to the workflow file
    workflow_file = Path(__file__).parent.parent / "workflows" / "Lead_Scoring.json"
    
    print("🔧 N8N Workflow Debugger - Full Analysis")
    print("=" * 60)
    
    try:
        with open(workflow_file, 'r') as f:
            workflow = json.load(f)
    except FileNotFoundError:
        print(f"❌ Workflow file not found: {workflow_file}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in workflow file: {e}")
        return

    print("🔍 Analyzing N8N Workflow Execution Flow")
    print("=" * 60)
    
    nodes = workflow.get('nodes', [])
    connections = workflow.get('connections', {})
    
    # Count different types of nodes
    conditional_nodes = []
    nodes_with_references = []
    issues = []
    
    for node in nodes:
        if node.get('type') == 'n8n-nodes-base.if':
            conditional_nodes.append(node['name'])
            
    # Look for nodes that reference other nodes in expressions
    for node in nodes:
        node_params = json.dumps(node.get('parameters', {}))
        if "$(" in node_params and ")" in node_params:
            nodes_with_references.append(node['name'])
    
    print(f"\n📊 Workflow Overview:")
    print(f"   Total nodes: {len(nodes)}")
    print(f"   Conditional nodes: {len(conditional_nodes)}")
    print(f"   Nodes with references: {len(nodes_with_references)}")
    print(f"   Issues found: {len(issues)}")
    
    if conditional_nodes:
        print(f"\n🔀 Conditional Nodes:")
        for node in conditional_nodes:
            node_data = next((n for n in nodes if n['name'] == node), {})
            node_id = node_data.get('id', 'unknown')
            print(f"   - {node} (ID: {node_id})")
    
    # Find trigger nodes
    trigger_nodes = []
    for node in nodes:
        node_type = node.get('type', '')
        if any(trigger in node_type for trigger in ['webhook', 'cron', 'trigger']):
            trigger_nodes.append(node['name'])
    
    print(f"🚀 Trigger nodes: {trigger_nodes}")
    
    # Build execution paths
    def trace_path(start_node, visited=None, path=None):
        if visited is None:
            visited = set()
        if path is None:
            path = []
            
        if start_node in visited:
            return [path + [start_node]]  # Cycle detected
            
        visited.add(start_node)
        path.append(start_node)
        
        if start_node not in connections:
            return [path]
            
        all_paths = []
        main_connections = connections[start_node].get('main', [[]])
        
        for connection_group in main_connections:
            if not connection_group:
                all_paths.append(path[:])
                continue
                
            for connection in connection_group:
                next_node = connection['node']
                sub_paths = trace_path(next_node, visited.copy(), path[:])
                all_paths.extend(sub_paths)
                
        return all_paths
    
    print(f"\n🗺️  Execution Paths:")
    for trigger in trigger_nodes:
        paths = trace_path(trigger)
        for path in paths[:2]:  # Show first 2 paths to avoid spam
            path_str = " → ".join(path)
            print(f"   {path_str}")
    
    # Test backend connectivity
    print(f"\n🧪 Testing Workflow with Backend API")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print(f"\n🧪 Backend Test Result:")
            print(f"   Status: ✅ PASS")
        else:
            print(f"\n🧪 Backend Test Result:")
            print(f"   Status: ❌ FAIL - HTTP {response.status_code}")
    except Exception as e:
        print(f"\n🧪 Backend Test Result:")
        print(f"   Status: ❌ FAIL - {str(e)}")

if __name__ == "__main__":
    analyze_workflow() 