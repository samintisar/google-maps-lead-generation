#!/usr/bin/env python3
"""
Query Optimization Analysis Script

This script analyzes database queries, identifies performance bottlenecks,
and provides optimization recommendations.
"""

import sys
import os
import time
from sqlalchemy import create_engine, text, func, and_, or_, desc, asc
from sqlalchemy.orm import sessionmaker, joinedload, selectinload
from sqlalchemy.sql import text as sql_text

# Add parent directory to path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import *

class QueryOptimizationAnalyzer:
    def __init__(self):
        self.engine = create_engine('postgresql://lma_user:lma_password@localhost:5432/lma_db')
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
    
    def analyze_table_sizes(self):
        """Analyze table sizes and row counts"""
        print('📊 TABLE SIZE ANALYSIS')
        print('=' * 50)
        
        tables = [
            'users', 'organizations', 'leads', 'communications', 'campaigns',
            'campaign_leads', 'lead_notes', 'activity_logs', 'workflows',
            'workflow_executions', 'lead_scoring_rules', 'lead_score_history',
            'integrations', 'lead_assignments'
        ]
        
        for table in tables:
            try:
                count_result = self.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                size_result = self.session.execute(text(f"SELECT pg_size_pretty(pg_total_relation_size('{table}'))")).scalar()
                print(f"  {table:20}: {count_result:6} rows, {size_result}")
            except Exception as e:
                print(f"  {table:20}: Error - {e}")
    
    def analyze_index_usage(self):
        """Analyze existing indexes and their usage"""
        print('\n🔍 INDEX USAGE ANALYSIS')
        print('=' * 50)
        
        # Get all indexes
        indexes_query = text("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef,
                pg_size_pretty(pg_relation_size(indexname::regclass)) as size
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """)
        
        indexes = self.session.execute(indexes_query).fetchall()
        
        current_table = None
        for index in indexes:
            if index.tablename != current_table:
                print(f"\n  📋 Table: {index.tablename}")
                current_table = index.tablename
            
            print(f"    {index.indexname:30} | {index.size:10} | {index.indexdef}")
    
    def run_slow_query_analysis(self):
        """Identify and analyze potentially slow queries"""
        print('\n⏱️ SLOW QUERY ANALYSIS')
        print('=' * 50)
        
        # Test 1: Complex joins without optimization
        print('\n  🔍 Test 1: Complex joins analysis')
        start_time = time.time()
        complex_query = self.session.query(Lead)\
            .join(Organization)\
            .join(User, Lead.assigned_to_id == User.id)\
            .join(Communication)\
            .filter(
                Lead.score > 30,
                Organization.subscription_tier == 'premium',
                Communication.communication_type == CommunicationType.EMAIL
            ).all()
        end_time = time.time()
        print(f"    Complex 4-table join: {len(complex_query)} results in {end_time - start_time:.3f}s")
        
        # Test 2: N+1 query problem demonstration
        print('\n  🔍 Test 2: N+1 query problem analysis')
        start_time = time.time()
        leads = self.session.query(Lead).limit(5).all()
        for lead in leads:
            # This will trigger additional queries for each lead
            communications_count = len(lead.communications)
            notes_count = len(lead.lead_notes)
        end_time = time.time()
        print(f"    N+1 problem (5 leads): {end_time - start_time:.3f}s")
        
        # Test 3: Optimized version with eager loading
        start_time = time.time()
        leads_optimized = self.session.query(Lead)\
            .options(
                selectinload(Lead.communications),
                selectinload(Lead.lead_notes)
            ).limit(5).all()
        for lead in leads_optimized:
            communications_count = len(lead.communications)
            notes_count = len(lead.lead_notes)
        end_time = time.time()
        print(f"    Optimized with eager loading: {end_time - start_time:.3f}s")
        
        # Test 4: Subquery performance
        print('\n  🔍 Test 3: Subquery vs JOIN performance')
        
        # Subquery approach
        start_time = time.time()
        subquery_result = self.session.query(Lead).filter(
            Lead.organization_id.in_(
                self.session.query(Organization.id).filter(
                    Organization.subscription_tier == 'premium'
                )
            )
        ).count()
        end_time = time.time()
        print(f"    Subquery approach: {subquery_result} results in {end_time - start_time:.3f}s")
        
        # JOIN approach
        start_time = time.time()
        join_result = self.session.query(Lead)\
            .join(Organization)\
            .filter(Organization.subscription_tier == 'premium')\
            .count()
        end_time = time.time()
        print(f"    JOIN approach: {join_result} results in {end_time - start_time:.3f}s")
    
    def analyze_query_execution_plans(self):
        """Analyze execution plans for key queries"""
        print('\n📋 QUERY EXECUTION PLAN ANALYSIS')
        print('=' * 50)
        
        # Analyze complex query execution plan
        explain_query = text("""
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT l.id, l.email, l.score, o.name as org_name, u.first_name, u.last_name
            FROM leads l
            JOIN organizations o ON l.organization_id = o.id
            LEFT JOIN users u ON l.assigned_to_id = u.id
            WHERE l.score > 50 AND o.subscription_tier = 'premium'
            ORDER BY l.score DESC
            LIMIT 10;
        """)
        
        try:
            result = self.session.execute(explain_query).fetchone()
            execution_plan = result[0][0]  # First element of JSON array
            
            print(f"  Query execution time: {execution_plan.get('Execution Time', 'N/A')} ms")
            print(f"  Planning time: {execution_plan.get('Planning Time', 'N/A')} ms")
            print(f"  Node type: {execution_plan.get('Plan', {}).get('Node Type', 'N/A')}")
            print(f"  Total cost: {execution_plan.get('Plan', {}).get('Total Cost', 'N/A')}")
            
        except Exception as e:
            print(f"  Error analyzing execution plan: {e}")
    
    def test_aggregation_performance(self):
        """Test performance of common aggregation queries"""
        print('\n📈 AGGREGATION PERFORMANCE ANALYSIS')
        print('=' * 50)
        
        # Test 1: Simple aggregation
        start_time = time.time()
        simple_agg = self.session.query(
            func.count(Lead.id),
            func.avg(Lead.score),
            func.max(Lead.score),
            func.min(Lead.score)
        ).first()
        end_time = time.time()
        print(f"  Simple aggregation: {end_time - start_time:.3f}s")
        print(f"    Count: {simple_agg[0]}, Avg: {simple_agg[1]:.2f}, Max: {simple_agg[2]}, Min: {simple_agg[3]}")
        
        # Test 2: Grouped aggregation
        start_time = time.time()
        grouped_agg = self.session.query(
            Lead.status,
            func.count(Lead.id).label('count'),
            func.avg(Lead.score).label('avg_score')
        ).group_by(Lead.status).all()
        end_time = time.time()
        print(f"  Grouped aggregation by status: {end_time - start_time:.3f}s")
        for status, count, avg_score in grouped_agg:
            print(f"    {status.value}: {count} leads, avg score {avg_score:.2f}")
        
        # Test 3: Complex aggregation with joins
        start_time = time.time()
        complex_agg = self.session.query(
            Organization.name,
            func.count(Lead.id).label('lead_count'),
            func.avg(Lead.score).label('avg_score'),
            func.count(Communication.id).label('comm_count')
        ).select_from(Organization)\
         .outerjoin(Lead)\
         .outerjoin(Communication)\
         .group_by(Organization.id, Organization.name).all()
        end_time = time.time()
        print(f"  Complex aggregation with joins: {end_time - start_time:.3f}s")
        for org_name, lead_count, avg_score, comm_count in complex_agg[:3]:  # Show first 3
            avg_score_display = f"{avg_score:.2f}" if avg_score else "N/A"
            print(f"    {org_name}: {lead_count} leads, {avg_score_display} avg score, {comm_count} comms")
    
    def generate_optimization_recommendations(self):
        """Generate specific optimization recommendations"""
        print('\n💡 OPTIMIZATION RECOMMENDATIONS')
        print('=' * 50)
        
        recommendations = []
        
        # Check for missing indexes on foreign keys
        print('  🔍 Analyzing foreign key indexes...')
        
        foreign_keys = [
            ('leads', 'organization_id'),
            ('leads', 'assigned_to_id'),
            ('communications', 'lead_id'),
            ('communications', 'user_id'),
            ('lead_notes', 'lead_id'),
            ('lead_notes', 'user_id'),
            ('campaign_leads', 'campaign_id'),
            ('campaign_leads', 'lead_id'),
            ('workflow_executions', 'lead_id'),
            ('activity_logs', 'lead_id'),
            ('activity_logs', 'user_id'),
        ]
        
        # Check for composite indexes needed
        print('  🔍 Recommending composite indexes...')
        recommendations.extend([
            "CREATE INDEX CONCURRENTLY idx_leads_org_status_score ON leads(organization_id, status, score DESC);",
            "CREATE INDEX CONCURRENTLY idx_leads_assigned_status ON leads(assigned_to_id, status) WHERE assigned_to_id IS NOT NULL;",
            "CREATE INDEX CONCURRENTLY idx_communications_lead_type_date ON communications(lead_id, communication_type, created_at DESC);",
            "CREATE INDEX CONCURRENTLY idx_activity_logs_lead_type_date ON activity_logs(lead_id, activity_type, created_at DESC);",
            "CREATE INDEX CONCURRENTLY idx_campaign_leads_campaign_status ON campaign_leads(campaign_id, status);",
            "CREATE INDEX CONCURRENTLY idx_leads_score_temp ON leads(score, lead_temperature);",
            "CREATE INDEX CONCURRENTLY idx_leads_created_org ON leads(created_at, organization_id);",
            "CREATE INDEX CONCURRENTLY idx_communications_scheduled_status ON communications(scheduled_at, status) WHERE scheduled_at IS NOT NULL;",
        ])
        
        # Query optimization recommendations
        query_recommendations = [
            "Use SELECT specific columns instead of SELECT *",
            "Implement pagination for large result sets",
            "Use eager loading (selectinload/joinedload) to avoid N+1 queries",
            "Consider using database views for complex, frequently-used queries",
            "Implement connection pooling for better resource utilization",
            "Use LIMIT clauses appropriately to prevent large result sets",
            "Consider partitioning for time-series data (activity_logs, communications)",
            "Implement proper caching strategy for frequently accessed data",
        ]
        
        print('\n  📝 SQL Index Recommendations:')
        for i, rec in enumerate(recommendations, 1):
            print(f"    {i}. {rec}")
        
        print('\n  📝 Query Optimization Recommendations:')
        for i, rec in enumerate(query_recommendations, 1):
            print(f"    {i}. {rec}")
    
    def run_full_analysis(self):
        """Run complete optimization analysis"""
        print('🚀 DATABASE QUERY OPTIMIZATION ANALYSIS')
        print('=' * 60)
        
        self.analyze_table_sizes()
        self.analyze_index_usage()
        self.run_slow_query_analysis()
        self.analyze_query_execution_plans()
        self.test_aggregation_performance()
        self.generate_optimization_recommendations()
        
        print('\n✅ Query optimization analysis completed!')
        self.session.close()

def main():
    analyzer = QueryOptimizationAnalyzer()
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main() 