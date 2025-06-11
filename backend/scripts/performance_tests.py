"""
Database Performance Testing Script

Tests the effectiveness of database optimizations by running
representative queries and measuring performance improvements.
"""

import time
import asyncio
import statistics
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lma_user:lma_password@localhost:15432/lma_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class PerformanceTests:
    """Database performance testing suite"""
    
    def __init__(self):
        self.session = SessionLocal()
        self.results = {}
    
    def time_query(self, name: str, query: str, iterations: int = 5) -> Dict[str, Any]:
        """Time a query execution multiple times and return statistics"""
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            try:
                result = self.session.execute(text(query))
                row_count = len(result.fetchall())
                end_time = time.time()
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                times.append(execution_time)
            except Exception as e:
                print(f"Error executing {name}: {e}")
                return {"error": str(e)}
        
        return {
            "query_name": name,
            "iterations": iterations,
            "times_ms": times,
            "avg_time_ms": statistics.mean(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "median_time_ms": statistics.median(times),
            "row_count": row_count if 'row_count' in locals() else 0
        }
    
    def explain_query(self, name: str, query: str) -> Dict[str, Any]:
        """Get query execution plan"""
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        try:
            result = self.session.execute(text(explain_query))
            plan = result.fetchone()[0][0]
            return {
                "query_name": name,
                "execution_plan": plan,
                "total_cost": plan.get("Total Cost", 0),
                "actual_time": plan.get("Actual Total Time", 0),
                "planning_time": plan.get("Planning Time", 0),
                "execution_time": plan.get("Execution Time", 0)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def test_lead_dashboard_queries(self):
        """Test lead dashboard performance - common business queries"""
        print("🔍 Testing Lead Dashboard Queries...")
        
        # Test 1: Organization lead summary (should use idx_leads_dashboard_summary)
        query1 = """
        SELECT organization_id, status, COUNT(*) as lead_count, AVG(score) as avg_score
        FROM leads 
        WHERE organization_id = 1 AND status IN ('new', 'contacted', 'qualified')
        GROUP BY organization_id, status
        """
        self.results["lead_summary"] = self.time_query("Lead Summary by Status", query1)
        
        # Test 2: Lead assignment queue (should use idx_leads_assignable)
        query2 = """
        SELECT id, first_name, last_name, company, score, created_at
        FROM leads 
        WHERE organization_id = 1 
        AND status IN ('new', 'contacted', 'qualified') 
        AND assigned_to_id IS NULL
        ORDER BY score DESC, created_at DESC
        LIMIT 20
        """
        self.results["assignment_queue"] = self.time_query("Lead Assignment Queue", query2)
        
        # Test 3: Lead scoring analysis (should use idx_leads_org_score_temp)
        query3 = """
        SELECT lead_temperature, AVG(score) as avg_score, COUNT(*) as lead_count
        FROM leads 
        WHERE organization_id = 1 AND score > 0
        GROUP BY lead_temperature
        ORDER BY avg_score DESC
        """
        self.results["scoring_analysis"] = self.time_query("Lead Scoring Analysis", query3)
    
    def test_communication_queries(self):
        """Test communication-related query performance"""
        print("📞 Testing Communication Queries...")
        
        # Test 1: Communication history for lead (should use idx_comms_lead_type_completed)
        query1 = """
        SELECT communication_type, COUNT(*) as comm_count, MAX(completed_at) as last_comm
        FROM communications 
        WHERE lead_id = 1 AND status = 'completed'
        GROUP BY communication_type
        ORDER BY last_comm DESC
        """
        self.results["comm_history"] = self.time_query("Communication History", query1)
        
        # Test 2: User scheduled communications (should use idx_comms_user_scheduled)
        query2 = """
        SELECT id, lead_id, communication_type, scheduled_at, subject
        FROM communications 
        WHERE user_id = 1 AND status = 'scheduled' AND scheduled_at IS NOT NULL
        ORDER BY scheduled_at ASC
        LIMIT 10
        """
        self.results["scheduled_comms"] = self.time_query("Scheduled Communications", query2)
    
    def test_json_search_queries(self):
        """Test JSON field search performance with GIN indexes"""
        print("🔍 Testing JSON Search Queries...")
        
        # Test 1: Lead tags search (should use idx_leads_tags_gin)
        query1 = """
        SELECT id, first_name, last_name, tags
        FROM leads 
        WHERE tags @> '["test"]'
        """
        self.results["tag_search"] = self.time_query("Lead Tags Search", query1)
        
        # Test 2: Custom fields search (should use idx_leads_custom_fields_gin)
        query2 = """
        SELECT id, first_name, last_name, custom_fields
        FROM leads 
        WHERE custom_fields ? 'industry'
        """
        self.results["custom_fields"] = self.time_query("Custom Fields Search", query2)
    
    def test_time_series_queries(self):
        """Test time-series performance optimizations"""
        print("⏰ Testing Time-Series Queries...")
        
        # Test 1: Recent activity logs (should use idx_activity_logs_monthly)
        query1 = """
        SELECT activity_type, COUNT(*) as activity_count
        FROM activity_logs 
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY activity_type
        ORDER BY activity_count DESC
        """
        self.results["recent_activities"] = self.time_query("Recent Activity Logs", query1)
        
        # Test 2: Lead score changes (should use idx_lead_score_recent)
        query2 = """
        SELECT lead_id, COUNT(*) as score_changes, MAX(created_at) as last_change
        FROM lead_score_history 
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY lead_id
        ORDER BY score_changes DESC
        LIMIT 10
        """
        self.results["score_changes"] = self.time_query("Lead Score Changes", query2)
    
    def test_complex_reporting_queries(self):
        """Test complex reporting queries using views"""
        print("📊 Testing Complex Reporting Queries...")
        
        # Test 1: Lead performance summary view
        query1 = """
        SELECT status, source, lead_count, avg_score, avg_age_days
        FROM v_lead_performance_summary
        WHERE organization_id = 1
        ORDER BY lead_count DESC
        """
        self.results["performance_summary"] = self.time_query("Lead Performance Summary", query1)
        
        # Test 2: User activity summary view
        query2 = """
        SELECT user_id, role, total_activities, communication_count, assigned_leads
        FROM v_user_activity_summary
        WHERE organization_id = 1
        ORDER BY total_activities DESC
        """
        self.results["user_activity"] = self.time_query("User Activity Summary", query2)
        
        # Test 3: Organization health metrics view
        query3 = """
        SELECT name, active_users, total_leads, active_leads, won_leads, avg_lead_score
        FROM v_organization_health
        ORDER BY total_leads DESC
        """
        self.results["org_health"] = self.time_query("Organization Health", query3)
    
    def run_query_plan_analysis(self):
        """Analyze query execution plans for key queries"""
        print("🔍 Analyzing Query Execution Plans...")
        
        key_queries = {
            "lead_dashboard": """
                SELECT organization_id, status, COUNT(*), AVG(score) 
                FROM leads 
                WHERE organization_id = 1 AND status IN ('new', 'contacted', 'qualified')
                GROUP BY organization_id, status
            """,
            "communication_history": """
                SELECT communication_type, COUNT(*) 
                FROM communications 
                WHERE lead_id = 1 AND status = 'completed'
                GROUP BY communication_type
            """,
            "assignment_queue": """
                SELECT id, score, created_at 
                FROM leads 
                WHERE organization_id = 1 AND assigned_to_id IS NULL
                ORDER BY score DESC, created_at DESC
                LIMIT 20
            """
        }
        
        for name, query in key_queries.items():
            plan = self.explain_query(f"{name}_plan", query)
            self.results[f"{name}_execution_plan"] = plan
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("🚀 Starting Database Performance Tests...")
        print("=" * 60)
        
        # Run test suites
        self.test_lead_dashboard_queries()
        self.test_communication_queries()
        self.test_json_search_queries()
        self.test_time_series_queries()
        self.test_complex_reporting_queries()
        self.run_query_plan_analysis()
        
        print("✅ Performance Tests Complete!")
        return self.results
    
    def generate_report(self):
        """Generate a performance test report"""
        if not self.results:
            print("No test results available. Run tests first.")
            return
        
        print("\n" + "=" * 80)
        print("DATABASE PERFORMANCE TEST REPORT")
        print("=" * 80)
        
        # Summary statistics
        all_times = []
        for test_name, result in self.results.items():
            if "times_ms" in result:
                all_times.extend(result["times_ms"])
        
        if all_times:
            print(f"\n📈 OVERALL PERFORMANCE SUMMARY:")
            print(f"   Total queries tested: {len([r for r in self.results.values() if 'times_ms' in r])}")
            print(f"   Average query time: {statistics.mean(all_times):.2f}ms")
            print(f"   Fastest query: {min(all_times):.2f}ms")
            print(f"   Slowest query: {max(all_times):.2f}ms")
        
        # Detailed results
        print(f"\n📊 DETAILED TEST RESULTS:")
        for test_name, result in self.results.items():
            if "times_ms" in result:
                print(f"\n   {result['query_name']}:")
                print(f"      Average: {result['avg_time_ms']:.2f}ms")
                print(f"      Range: {result['min_time_ms']:.2f}ms - {result['max_time_ms']:.2f}ms")
                print(f"      Rows: {result['row_count']}")
        
        # Performance recommendations
        print(f"\n🎯 PERFORMANCE RECOMMENDATIONS:")
        slow_queries = [r for r in self.results.values() 
                       if 'avg_time_ms' in r and r['avg_time_ms'] > 100]
        
        if slow_queries:
            print("   ⚠️  Queries taking >100ms:")
            for query in slow_queries:
                print(f"      - {query['query_name']}: {query['avg_time_ms']:.2f}ms")
        else:
            print("   ✅ All queries performing well (<100ms average)")
        
        print("\n" + "=" * 80)
    
    def close(self):
        """Close database session"""
        self.session.close()

def main():
    """Run performance tests"""
    tester = PerformanceTests()
    try:
        tester.run_all_tests()
        tester.generate_report()
    finally:
        tester.close()

if __name__ == "__main__":
    main() 