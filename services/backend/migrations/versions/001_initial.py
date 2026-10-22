"""Initial migration: all MVP entities

Revision ID: 001_initial
Revises: 
Create Date: 2026-10-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON, ENUM

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    document_status = ENUM(
        'active', 'deleted', 'archived',
        name='document_status', create_type=True
    )
    document_status.create(op.get_bind(), checkfirst=True)

    ingestion_status = ENUM(
        'uploaded', 'validating', 'parsing', 'chunking', 'embedding', 'indexing',
        'ready', 'rejected', 'failed', 'cancelled', 'ready_with_warnings',
        name='ingestion_status', create_type=True
    )
    ingestion_status.create(op.get_bind(), checkfirst=True)

    ingestion_job_state = ENUM(
        'pending', 'running', 'succeeded', 'failed', 'cancelled',
        name='ingestion_job_state', create_type=True
    )
    ingestion_job_state.create(op.get_bind(), checkfirst=True)

    ingestion_job_stage = ENUM(
        'validating', 'parsing', 'chunking', 'embedding', 'indexing', 'finalizing',
        name='ingestion_job_stage', create_type=True
    )
    ingestion_job_stage.create(op.get_bind(), checkfirst=True)

    ingestion_error_category = ENUM(
        'validation', 'parsing', 'chunking', 'embedding', 'indexing', 'internal', 'timeout', 'resource',
        name='ingestion_error_category', create_type=True
    )
    ingestion_error_category.create(op.get_bind(), checkfirst=True)

    index_status = ENUM(
        'building', 'ready', 'deprecated', 'failed',
        name='index_status', create_type=True
    )
    index_status.create(op.get_bind(), checkfirst=True)

    dataset_version_status = ENUM(
        'draft', 'published', 'archived',
        name='dataset_version_status', create_type=True
    )
    dataset_version_status.create(op.get_bind(), checkfirst=True)

    experiment_status = ENUM(
        'active', 'archived',
        name='experiment_status', create_type=True
    )
    experiment_status.create(op.get_bind(), checkfirst=True)

    experiment_run_status = ENUM(
        'pending', 'running', 'completed', 'failed', 'cancelled',
        name='experiment_run_status', create_type=True
    )
    experiment_run_status.create(op.get_bind(), checkfirst=True)

    sample_status = ENUM(
        'completed', 'failed', 'skipped',
        name='sample_status', create_type=True
    )
    sample_status.create(op.get_bind(), checkfirst=True)

    answer_status = ENUM(
        'answered', 'insufficient_evidence', 'failed',
        name='answer_status', create_type=True
    )
    answer_status.create(op.get_bind(), checkfirst=True)

    audit_event_type = ENUM(
        'document_uploaded', 'document_deleted', 'document_reindexed',
        'dataset_created', 'dataset_version_published',
        'experiment_created', 'experiment_run_started',
        'experiment_run_completed', 'experiment_run_failed',
        'config_changed',
        name='audit_event_type', create_type=True
    )
    audit_event_type.create(op.get_bind(), checkfirst=True)

    # Documents table
    op.create_table(
        'documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('display_name', sa.String(500), nullable=False),
        sa.Column('media_type', sa.String(100), nullable=False),
        sa.Column('status', sa.Enum('active', 'deleted', 'archived', name='document_status'), nullable=False, server_default='active'),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_documents_status', 'documents', ['status'])
    op.create_index('ix_documents_created_at', 'documents', ['created_at'])
    op.create_index('ix_documents_content_hash_size', 'documents', ['content_hash', 'size_bytes'])

    # Document versions table
    op.create_table(
        'document_versions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', sa.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('parser_version', sa.String(100), nullable=False),
        sa.Column('parser_metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('storage_ref', sa.Text(), nullable=False),
        sa.Column('page_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ingestion_status', sa.Enum('uploaded', 'validating', 'parsing', 'chunking', 'embedding', 'indexing', 'ready', 'rejected', 'failed', 'cancelled', 'ready_with_warnings', name='ingestion_status'), nullable=False, server_default='uploaded'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint('uq_document_version', 'document_versions', ['document_id', 'version_number'])
    op.create_index('ix_document_versions_document_id', 'document_versions', ['document_id'])
    op.create_index('ix_document_versions_ingestion_status', 'document_versions', ['ingestion_status'])
    op.create_index('ix_document_versions_content_hash', 'document_versions', ['content_hash'])

    # Ingestion jobs table
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_version_id', sa.UUID(as_uuid=True), sa.ForeignKey('document_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attempt', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('state', sa.Enum('pending', 'running', 'succeeded', 'failed', 'cancelled', name='ingestion_job_state'), nullable=False, server_default='pending'),
        sa.Column('stage', sa.Enum('validating', 'parsing', 'chunking', 'embedding', 'indexing', 'finalizing', name='ingestion_job_stage'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_category', sa.Enum('validation', 'parsing', 'chunking', 'embedding', 'indexing', 'internal', 'timeout', 'resource', name='ingestion_error_category'), nullable=True),
        sa.Column('user_message', sa.Text(), nullable=True),
        sa.Column('technical_details', sa.JSON(), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint('uq_ingestion_job_attempt', 'ingestion_jobs', ['document_version_id', 'attempt'])
    op.create_index('ix_ingestion_jobs_document_version_id', 'ingestion_jobs', ['document_version_id'])
    op.create_index('ix_ingestion_jobs_state', 'ingestion_jobs', ['state'])
    op.create_index('ix_ingestion_jobs_started_at', 'ingestion_jobs', ['started_at'])

    # Index versions table
    op.create_table(
        'index_versions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('corpus_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('chunking_config_hash', sa.String(64), nullable=False),
        sa.Column('embedding_provider', sa.String(100), nullable=False),
        sa.Column('embedding_model', sa.String(100), nullable=False),
        sa.Column('embedding_version', sa.String(100), nullable=False),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('vector_collection', sa.String(200), nullable=False),
        sa.Column('status', sa.Enum('building', 'ready', 'deprecated', 'failed', name='index_status'), nullable=False, server_default='building'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint(
        'uq_index_version_config',
        'index_versions',
        ['corpus_id', 'chunking_config_hash', 'embedding_provider', 'embedding_model', 'embedding_version', 'embedding_dimension']
    )
    op.create_index('ix_index_versions_corpus_id', 'index_versions', ['corpus_id'])
    op.create_index('ix_index_versions_status', 'index_versions', ['status'])
    op.create_index('ix_index_versions_embedding', 'index_versions', ['embedding_provider', 'embedding_model', 'embedding_version'])

    # Chunks table
    op.create_table(
        'chunks',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_version_id', sa.UUID(as_uuid=True), sa.ForeignKey('document_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('corpus_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text_hash', sa.String(64), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('start_offset', sa.Integer(), nullable=True),
        sa.Column('end_offset', sa.Integer(), nullable=True),
        sa.Column('chunker_config_hash', sa.String(64), nullable=False),
        sa.Column('embedding_provider', sa.String(100), nullable=False),
        sa.Column('embedding_model', sa.String(100), nullable=False),
        sa.Column('embedding_version', sa.String(100), nullable=False),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('index_version', sa.UUID(as_uuid=True), sa.ForeignKey('index_versions.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_version_id'], ['document_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['index_version'], ['index_versions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint(
        'uq_chunk_doc_ver_index_config',
        'chunks',
        ['document_version_id', 'chunk_index', 'chunker_config_hash']
    )
    op.create_index('ix_chunks_document_version_id', 'chunks', ['document_version_id'])
    op.create_index('ix_chunks_corpus_id', 'chunks', ['corpus_id'])
    op.create_index('ix_chunks_index_version', 'chunks', ['index_version'])
    op.create_index('ix_chunks_text_hash', 'chunks', ['text_hash'])
    op.create_index('ix_chunks_embedding', 'chunks', ['embedding_provider', 'embedding_model', 'embedding_version'])

    # Datasets table
    op.create_table(
        'datasets',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_datasets_name', 'datasets', ['name'])

    # Dataset versions table
    op.create_table(
        'dataset_versions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_id', sa.UUID(as_uuid=True), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('schema_version', sa.String(20), server_default='1.0', nullable=False),
        sa.Column('hash', sa.String(64), nullable=False),
        sa.Column('provenance', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('draft', 'published', 'archived', name='dataset_version_status'), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint('uq_dataset_version', 'dataset_versions', ['dataset_id', 'version'])
    op.create_index('ix_dataset_versions_dataset_id', 'dataset_versions', ['dataset_id'])
    op.create_index('ix_dataset_versions_status', 'dataset_versions', ['status'])

    # Dataset samples table
    op.create_table(
        'dataset_samples',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('dataset_version_id', sa.UUID(as_uuid=True), sa.ForeignKey('dataset_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sample_id', sa.String(100), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('corpus_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('relevant_document_ids', sa.ARRAY(sa.UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('relevant_chunk_ids', sa.ARRAY(sa.UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('relevance_grades', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('reference_answer', sa.Text(), nullable=True),
        sa.Column('expected_citation_ids', sa.ARRAY(sa.UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('answerable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('tags', sa.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('provenance', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['dataset_version_id'], ['dataset_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint('uq_dataset_sample', 'dataset_samples', ['dataset_version_id', 'sample_id'])
    op.create_index('ix_dataset_samples_dataset_version_id', 'dataset_samples', ['dataset_version_id'])
    op.create_index('ix_dataset_samples_answerable', 'dataset_samples', ['answerable'])
    op.create_index('ix_dataset_samples_corpus_id', 'dataset_samples', ['corpus_id'])

    # Experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config_manifest', sa.JSON(), nullable=False),
        sa.Column('config_hash', sa.String(64), unique=True, nullable=False),
        sa.Column('status', sa.Enum('active', 'archived', name='experiment_status'), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_experiments_config_hash', 'experiments', ['config_hash'])
    op.create_index('ix_experiments_status', 'experiments', ['status'])

    # Experiment runs table
    op.create_table(
        'experiment_runs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('experiment_id', sa.UUID(as_uuid=True), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dataset_version_id', sa.UUID(as_uuid=True), sa.ForeignKey('dataset_versions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('index_version_id', sa.UUID(as_uuid=True), sa.ForeignKey('index_versions.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'cancelled', name='experiment_run_status'), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('software_version', sa.String(100), nullable=False),
        sa.Column('environment', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('total_samples', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_samples', sa.Integer(), server_default='0', nullable=False),
        sa.Column('failed_samples', sa.Integer(), server_default='0', nullable=False),
        sa.Column('skipped_samples', sa.Integer(), server_default='0', nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_version_id'], ['dataset_versions.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['index_version_id'], ['index_versions.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_experiment_runs_experiment_id', 'experiment_runs', ['experiment_id'])
    op.create_index('ix_experiment_runs_dataset_version_id', 'experiment_runs', ['dataset_version_id'])
    op.create_index('ix_experiment_runs_index_version_id', 'experiment_runs', ['index_version_id'])
    op.create_index('ix_experiment_runs_status', 'experiment_runs', ['status'])
    op.create_index('ix_experiment_runs_started_at', 'experiment_runs', ['started_at'])

    # Sample results table
    op.create_table(
        'sample_results',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('experiment_run_id', sa.UUID(as_uuid=True), sa.ForeignKey('experiment_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sample_id', sa.UUID(as_uuid=True), sa.ForeignKey('dataset_samples.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.Enum('completed', 'failed', 'skipped', name='sample_status'), nullable=False),
        sa.Column('retrieval_results', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('generation_result', sa.JSON(), nullable=True),
        sa.Column('citation_validation', sa.JSON(), nullable=True),
        sa.Column('error_category', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retrieval_latency_ms', sa.Integer(), nullable=True),
        sa.Column('generation_latency_ms', sa.Integer(), nullable=True),
        sa.Column('total_latency_ms', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['experiment_run_id'], ['experiment_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sample_id'], ['dataset_samples.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint('uq_sample_result', 'sample_results', ['experiment_run_id', 'sample_id'])
    op.create_index('ix_sample_results_experiment_run_id', 'sample_results', ['experiment_run_id'])
    op.create_index('ix_sample_results_status', 'sample_results', ['status'])

    # Metric results table
    op.create_table(
        'metric_results',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('experiment_run_id', sa.UUID(as_uuid=True), sa.ForeignKey('experiment_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_version', sa.String(20), server_default='1.0', nullable=False),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('denominator', sa.Integer(), nullable=True),
        sa.Column('evaluator_metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('sample_count', sa.Integer(), nullable=False),
        sa.Column('failed_sample_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['experiment_run_id'], ['experiment_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint('uq_metric_result', 'metric_results', ['experiment_run_id', 'metric_name', 'metric_version'])
    op.create_index('ix_metric_results_experiment_run_id', 'metric_results', ['experiment_run_id'])
    op.create_index('ix_metric_results_metric_name', 'metric_results', ['metric_name'])

    # Answers table
    op.create_table(
        'answers',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('answered', 'insufficient_evidence', 'failed', name='answer_status'), nullable=False),
        sa.Column('limitations', sa.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('provider_metadata', sa.JSON(), nullable=False),
        sa.Column('latency_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_answers_created_at', 'answers', ['created_at'])
    op.create_index('ix_answers_status', 'answers', ['status'])

    # Citations table
    op.create_table(
        'citations',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('answer_id', sa.UUID(as_uuid=True), sa.ForeignKey('answers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', sa.UUID(as_uuid=True), sa.ForeignKey('chunks.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('document_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('document_version_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('source_title', sa.String(500), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['answer_id'], ['answers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_citations_answer_id', 'citations', ['answer_id'])
    op.create_index('ix_citations_chunk_id', 'citations', ['chunk_id'])

    # Audit events table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_type', sa.Enum('document_uploaded', 'document_deleted', 'document_reindexed', 'dataset_created', 'dataset_version_published', 'experiment_created', 'experiment_run_started', 'experiment_run_completed', 'experiment_run_failed', 'config_changed', name='audit_event_type'), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_identifier', sa.String(100), server_default='local', nullable=False),
        sa.Column('event_metadata', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_events_entity', 'audit_events', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_events_timestamp', 'audit_events', ['timestamp'])
    op.create_index('ix_audit_events_event_type', 'audit_events', ['event_type'])

    # Provider configurations table
    op.create_table(
        'provider_configurations',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('provider_type', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('version', sa.String(100), nullable=False),
        sa.Column('config', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_unique_constraint('uq_provider_config', 'provider_configurations', ['provider_type', 'provider', 'model', 'version'])
    op.create_index('ix_provider_configurations_type_active', 'provider_configurations', ['provider_type', 'is_active'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('provider_configurations')
    op.drop_table('audit_events')
    op.drop_table('citations')
    op.drop_table('answers')
    op.drop_table('metric_results')
    op.drop_table('sample_results')
    op.drop_table('experiment_runs')
    op.drop_table('experiments')
    op.drop_table('dataset_samples')
    op.drop_table('dataset_versions')
    op.drop_table('datasets')
    op.drop_table('chunks')
    op.drop_table('index_versions')
    op.drop_table('ingestion_jobs')
    op.drop_table('document_versions')
    op.drop_table('documents')

    # Drop ENUM types
    op.execute('DROP TYPE IF EXISTS audit_event_type')
    op.execute('DROP TYPE IF EXISTS answer_status')
    op.execute('DROP TYPE IF EXISTS sample_status')
    op.execute('DROP TYPE IF EXISTS experiment_run_status')
    op.execute('DROP TYPE IF EXISTS experiment_status')
    op.execute('DROP TYPE IF EXISTS dataset_version_status')
    op.execute('DROP TYPE IF EXISTS index_status')
    op.execute('DROP TYPE IF EXISTS ingestion_error_category')
    op.execute('DROP TYPE IF EXISTS ingestion_job_stage')
    op.execute('DROP TYPE IF EXISTS ingestion_job_state')
    op.execute('DROP TYPE IF EXISTS ingestion_status')
    op.execute('DROP TYPE IF EXISTS document_status')
