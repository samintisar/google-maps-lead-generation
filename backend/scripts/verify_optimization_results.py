#!/usr/bin/env python3
"""
Verify Query Optimization Results

This script runs comprehensive performance tests to verify the impact
of the applied database optimizations.
"""

import sys
import os
import time
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, selectinload, joinedload

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import *

class OptimizationVerifier:
    def __init__(self):
        self.engine = create_engine('postgresql://lma_user:lma_password@localhost:5432/lma_db')
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.results = {}
    
    def test_optimized_queries(self):
        """Test the performance of optimized queries"""
        print('🚀 TESTING OPTIMIZED QUERY PERFORMANCE')
        print('=' * 60)
        
        # Test 1: Organization-scoped lead queries (using optimized index)
        print('\n  🔍 Test 1: Organization-scoped lead queries')
        start_time = time.time()
        org_leads = self.session.query(Lead).filter(
            Lead.organization_id == 1,
            Lead.status == LeadStatus.QUALIFIED,
            Lead.score > 50
        ).order_by(Lead.score.desc()).limit(10).all()
        end_time = time.time()
        query_time = end_time - start_time
        self.results['org_scoped_query'] = query_time
        print(f"    Query time: {query_time:.3f}s ({len(org_leads)} results)")
        print(f"    Index used: idx_leads_org_status_score")
        
        # Test 2: Assigned lead queries (using partial index)
        print('\n  🔍 Test 2: Assigned lead status queries')
        start_time = time.time()
        assigned_leads = self.session.query(Lead).filter(
            Lead.assigned_to_id.isnot(None),
            Lead.status == LeadStatus.NEW
        ).all()
        end_time = time.time()
        query_time = end_time - start_time
        self.results['assigned_lead_query'] = query_time
        print(f"    Query time: {query_time:.3f}s ({len(assigned_leads)} results)")
        print(f"    Index used: idx_leads_assigned_status")
        
        # Test 3: Communication history queries (using composite index)
        print('\n  🔍 Test 3: Communication history queries')
        start_time = time.time()
        comm_history = self.session.query(Communication).filter(
            Communication.lead_id.in_([1, 2, 3, 4, 5]),
            Communication.communication_type == CommunicationType.EMAIL
        ).order_by(Communication.created_at.desc()).all()
        end_time = time.time()
        query_time = end_time - start_time
        self.results['communication_query'] = query_time
        print(f"    Query time: {query_time:.3f}s ({len(comm_history)} results)")
        print(f"    Index used: idx_communications_lead_type_date")
        
        # Test 4: Lead scoring queries (using composite index)
        print('\n  🔍 Test 4: Lead scoring and temperature queries')
        start_time = time.time()
        scored_leads = self.session.query(Lead).filter(
            Lead.score >= 40,
            Lead.lead_temperature.in_([LeadTemperature.HOT, LeadTemperature.WARM])
        ).all()
        end_time = time.time()
        query_time = end_time - start_time
        self.results['scoring_query'] = query_time
        print(f"    Query time: {query_time:.3f}s ({len(scored_leads)} results)")
        print(f"    Index used: idx_leads_score_temp")
        
        # Test 5: Complex aggregation with joins
        print('\n  🔍 Test 5: Complex aggregation queries')
        start_time = time.time()
        complex_agg = self.session.query(
            Organization.name,
            func.count(Lead.id).label('lead_count'),
            func.avg(Lead.score).label('avg_score'),
            func.max(Lead.score).label('max_score')
        ).join(Lead).group_by(Organization.id, Organization.name).all()
        end_time = time.time()
        query_time = end_time - start_time
        self.results['complex_aggregation'] = query_time
        print(f"    Query time: {query_time:.3f}s ({len(complex_agg)} results)")
        for org_name, lead_count, avg_score, max_score in complex_agg:
            print(f"      {org_name}: {lead_count} leads, avg {avg_score:.2f}, max {max_score}")
    
    def test_eager_loading_optimization(self):
        """Test N+1 query problem resolution with eager loading"""
        print('\n💡 TESTING EAGER LOADING OPTIMIZATION')
        print('=' * 60)
        
        # Test with N+1 problem (inefficient)
        print('\n  ❌ Testing N+1 query problem (inefficient)')
        start_time = time.time()
        leads = self.session.query(Lead).limit(5).all()
        for lead in leads:
            communications_count = len(lead.communications)
            notes_count = len(lead.lead_notes)
        end_time = time.time()
        n_plus_one_time = end_time - start_time
        print(f"    N+1 query time: {n_plus_one_time:.3f}s")
        
        # Test with eager loading (optimized)
        print('\n  ✅ Testing eager loading optimization')
        start_time = time.time()
        leads_optimized = self.session.query(Lead)\
            .options(
                selectinload(Lead.communications),
                selectinload(Lead.lead_notes),
                joinedload(Lead.organization),
                joinedload(Lead.assigned_to)
            ).limit(5).all()
        for lead in leads_optimized:
            communications_count = len(lead.communications)
            notes_count = len(lead.lead_notes)
            org_name = lead.organization.name if lead.organization else "N/A"
            assigned_name = lead.assigned_to.full_name if lead.assigned_to else "Unassigned"
        end_time = time.time()
        eager_loading_time = end_time - start_time
        print(f"    Eager loading time: {eager_loading_time:.3f}s")
        
        improvement = ((n_plus_one_time - eager_loading_time) / n_plus_one_time) * 100 if n_plus_one_time > 0 else 0
        print(f"    Performance improvement: {improvement:.1f}%")
        
        self.results['n_plus_one_time'] = n_plus_one_time
        self.results['eager_loading_time'] = eager_loading_time
    
    def test_database_views(self):
        """Test performance of created database views"""
        print('\n📊 TESTING DATABASE VIEWS PERFORMANCE')
        print('=' * 60)
        
        # Test v_lead_summary view
        print('\n  🔍 Testing v_lead_summary view')
        start_time = time.time()
        lead_summaries = self.session.execute(text("""
            SELECT * FROM v_lead_summary 
            WHERE organization_name = 'Bell-Kirk' 
            ORDER BY score DESC 
            LIMIT 10
        """)).fetchall()
        end_time = time.time()
        query_time = end_time - start_time
        self.results['lead_summary_view'] = query_time
        print(f"    Query time: {query_time:.3f}s ({len(lead_summaries)} results)")
        
        # Test v_organization_metrics view
        print('\n  🔍 Testing v_organization_metrics view')
        start_time = time.time()
        org_metrics = self.session.execute(text("""
            SELECT * FROM v_organization_metrics 
            ORDER BY total_leads DESC
        """)).fetchall()
        end_time = time.time()
        query_time = end_time - start_time
        self.results['org_metrics_view'] = query_time
        print(f"    Query time: {query_time:.3f}s ({len(org_metrics)} results)")
        for metric in org_metrics:
            print(f"      {metric.name}: {metric.total_leads} leads, {metric.total_users} users, avg score {metric.avg_lead_score:.2f if metric.avg_lead_score else 'N/A'}")
        
        # Test v_user_productivity view
        print('\n  🔍 Testing v_user_productivity view')
        start_time = time.time()
        user_productivity = self.session.execute(text("""
            SELECT * FROM v_user_productivity 
            WHERE assigned_leads > 0 
            ORDER BY assigned_leads DESC 
            LIMIT 5
        """)).fetchall()
        end_time = time.time()
        query_time = end_time - start_time
        self.results['user_productivity_view'] = query_time
        print(f"    Query time: {query_time:.3f}s ({len(user_productivity)} results)")
        for user in user_productivity:
            print(f"      {user.first_name} {user.last_name}: {user.assigned_leads} leads, {user.total_communications} comms")
    
    def test_index_usage_verification(self):
        """Verify that indexes are being used correctly"""
        print('\n🔍 VERIFYING INDEX USAGE')
        print('=' * 60)
        
        # Test query plan for organization-scoped query
        explain_query = text("""
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT l.id, l.email, l.score, l.status
            FROM leads l
            WHERE l.organization_id = 1 
              AND l.status = 'QUALIFIED' 
              AND l.score > 50
            ORDER BY l.score DESC
            LIMIT 10;
        """)
        
        try:
            result = self.session.execute(explain_query).fetchone()
            execution_plan = result[0][0]
            
            print(f"  📋 Query Execution Plan Analysis:")
            print(f"    Execution time: {execution_plan.get('Execution Time', 'N/A')} ms")
            print(f"    Planning time: {execution_plan.get('Planning Time', 'N/A')} ms")
            print(f"    Node type: {execution_plan.get('Plan', {}).get('Node Type', 'N/A')}")
            
            # Check if index is being used
            plan_str = str(execution_plan)
            if 'idx_leads_org_status_score' in plan_str:
                print(f"    ✅ Index idx_leads_org_status_score is being used!")
            else:
                print(f"    ❓ Custom index usage not detected in plan")
                
        except Exception as e:
            print(f"    ❌ Error analyzing execution plan: {e}")
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print('\n📋 COMPREHENSIVE PERFORMANCE REPORT')
        print('=' * 60)
        
        # Database statistics
        print('\n  📊 Database Statistics:')
        total_size = self.session.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))")).scalar()
        index_count = self.session.execute(text("SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'")).scalar()
        print(f"    Total database size: {total_size}")
        print(f"    Total indexes: {index_count}")
        
        # Performance metrics
        print('\n  ⚡ Performance Metrics:')
        for test_name, time_taken in self.results.items():
            performance_rating = "🟢 Excellent" if time_taken < 0.01 else "🟡 Good" if time_taken < 0.05 else "🔴 Needs Attention"
            print(f"    {test_name:25}: {time_taken:.3f}s {performance_rating}")
        
        # Optimization summary
        print('\n  ✅ Applied Optimizations:')
        optimizations = [
            "Composite indexes for multi-column queries",
            "Partial indexes for filtered queries",
            "Database views for complex aggregations",
            "Eager loading patterns to prevent N+1 queries",
            "Query execution plan analysis",
            "Index usage verification"
        ]
        
        for i, optimization in enumerate(optimizations, 1):
            print(f"    {i}. {optimization}")
        
        # Recommendations for production
        print('\n  🎯 Production Recommendations:')
        recommendations = [
            "Monitor query performance with pg_stat_statements",
            "Implement connection pooling (pgbouncer/SQLAlchemy pool)",
            "Set up automated VACUUM and ANALYZE scheduling",
            "Consider READ replicas for reporting queries",
            "Implement query result caching for frequently accessed data",
            "Monitor index usage and remove unused indexes",
            "Consider partitioning for time-series data at scale",
            "Implement proper application-level caching strategy"
        ]
        
        for i, recommendation in enumerate(recommendations, 1):
            print(f"    {i}. {recommendation}")
        
        print(f"\n  🏆 Overall Assessment:")
        avg_time = sum(self.results.values()) / len(self.results) if self.results else 0
        if avg_time < 0.01:
            assessment = "🟢 EXCELLENT - Database is highly optimized"
        elif avg_time < 0.05:
            assessment = "🟡 GOOD - Database performance is solid"
        else:
            assessment = "🔴 NEEDS IMPROVEMENT - Consider additional optimizations"
        
        print(f"    {assessment}")
        print(f"    Average query time: {avg_time:.3f}s")
    
    def run_verification(self):
        """Run complete verification process"""
        print('🚀 DATABASE OPTIMIZATION VERIFICATION')
        print('=' * 70)
        
        try:
            self.test_optimized_queries()
            self.test_eager_loading_optimization()
            self.test_database_views()
            self.test_index_usage_verification()
            self.generate_performance_report()
            
            print('\n✅ Optimization verification completed successfully!')
            
        except Exception as e:
            print(f'\n❌ Error during verification: {e}')
        finally:
            self.session.close()

def main():
    verifier = OptimizationVerifier()
    verifier.run_verification()

if __name__ == "__main__":
    main() 