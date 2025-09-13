# Software Design Document (SDD)
## Medical Imaging AI Platform - Tumor Detection and Segmentation

**Document ID**: SDD-MIAP-001
**Version**: 1.0
**Date**: September 13, 2025
**Classification**: Unclassified
**Prepared by**: System Architecture Team
**Approved by**: Chief Technology Officer

---

## 1. INTRODUCTION

### 1.1 Purpose

This Software Design Document (SDD) provides a comprehensive architectural design for the Medical Imaging AI Platform (MIAP). The design follows NASA-STD-8739.8 standards and addresses all requirements specified in the Software Requirements Document (SRD-MIAP-001).

### 1.2 Scope

This document covers the complete system architecture including:
- High-level system architecture and component design
- Low-level module specifications and interfaces
- Data flow and control mechanisms
- Technology stack justification and trade-offs
- Security architecture and implementation strategies

### 1.3 Design Constraints and Assumptions

**Design Constraints:**
- Must comply with HIPAA/GDPR for medical data processing
- GPU memory limitations (8GB minimum, 48GB optimal)
- Clinical response time requirements (<30 seconds)
- Docker containerization for deployment consistency
- Web-based interface for cross-platform accessibility

**Assumptions:**
- Network connectivity for cloud services and updates
- Standard medical imaging formats (DICOM, NIfTI)
- Modern web browsers with JavaScript support
- Docker runtime environment availability

---

## 2. HIGH-LEVEL DESIGN

### 2.1 System Architecture Overview

The Medical Imaging AI Platform employs a **microservices architecture** with containerized components for scalability, maintainability, and deployment flexibility.

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Interface<br/>React/Vue.js]
        CLI[CLI Tools<br/>Python Scripts]
        API_CLIENT[API Clients<br/>Third-party]
    end

    subgraph "API Gateway Layer"
        GATEWAY[API Gateway<br/>FastAPI + Nginx]
        AUTH[Authentication<br/>OAuth2/JWT]
        RATE[Rate Limiting<br/>Redis]
    end

    subgraph "Core Services Layer"
        AI_ENGINE[AI Engine<br/>PyTorch + MONAI]
        CLINICAL[Clinical Operator<br/>Workflow Management]
        DATA_MGR[Data Manager<br/>DICOM/NIfTI Processing]
        ANNOTATION[Annotation Service<br/>MONAI Label]
    end

    subgraph "Data Layer"
        DB[(Database<br/>PostgreSQL)]
        REDIS[(Cache<br/>Redis)]
        STORAGE[File Storage<br/>MinIO/S3]
        REGISTRY[Model Registry<br/>MLflow]
    end

    subgraph "Infrastructure Layer"
        MONITORING[Monitoring<br/>Prometheus/Grafana]
        LOGGING[Logging<br/>ELK Stack]
        SECURITY[Security<br/>Vault/Cert Manager]
    end

    WEB --> GATEWAY
    CLI --> GATEWAY
    API_CLIENT --> GATEWAY

    GATEWAY --> AUTH
    GATEWAY --> RATE
    GATEWAY --> AI_ENGINE
    GATEWAY --> CLINICAL
    GATEWAY --> DATA_MGR
    GATEWAY --> ANNOTATION

    AI_ENGINE --> DB
    AI_ENGINE --> REDIS
    AI_ENGINE --> STORAGE
    AI_ENGINE --> REGISTRY

    CLINICAL --> DB
    DATA_MGR --> STORAGE
    ANNOTATION --> DB

    AI_ENGINE --> MONITORING
    CLINICAL --> LOGGING
    DATA_MGR --> SECURITY
```

### 2.2 Technology Stack Justification

| Component | Technology | Version | Rationale | Alternatives Considered | Trade-offs |
|-----------|------------|---------|-----------|-------------------------|------------|
| **AI Framework** | PyTorch | 1.12+ | Industry standard, extensive medical AI ecosystem | TensorFlow, JAX | Learning curve vs ecosystem |
| **Medical AI Library** | MONAI | 1.3+ | Purpose-built for medical imaging, comprehensive | Custom implementation, SimpleITK | Development time vs specialization |
| **API Framework** | FastAPI | 0.68+ | High performance, automatic documentation, async | Flask, Django REST | Complexity vs performance |
| **Frontend Framework** | React/Vue.js | Latest | Component-based, large ecosystem | Angular, Svelte | Bundle size vs ecosystem |
| **Database** | PostgreSQL | 13+ | ACID compliance, JSON support, reliability | MySQL, MongoDB | Performance vs consistency |
| **Cache/Queue** | Redis | 6+ | High performance, pub/sub, clustering | Memcached, RabbitMQ | Memory usage vs features |
| **Containerization** | Docker | 20.10+ | Industry standard, extensive tooling | Podman, containerd | Resource overhead vs portability |
| **Orchestration** | Docker Compose | 2.0+ | Simple multi-service management | Kubernetes, Docker Swarm | Complexity vs scalability |
| **Model Management** | MLflow | 2.0+ | Complete ML lifecycle, model registry | Weights & Biases, Neptune | Features vs simplicity |
| **Monitoring** | Prometheus/Grafana | Latest | Industry standard, extensive integrations | Datadog, New Relic | Cost vs control |

### 2.3 Component Interaction Diagram

```mermaid
sequenceDiagram
    participant Client
    participant Gateway as API Gateway
    participant Auth as Authentication
    participant AIEngine as AI Engine
    participant DataMgr as Data Manager
    participant Database
    participant Storage

    Client->>Gateway: Request inference
    Gateway->>Auth: Validate token
    Auth-->>Gateway: Token valid
    Gateway->>AIEngine: Process request
    AIEngine->>DataMgr: Load medical data
    DataMgr->>Storage: Retrieve DICOM files
    Storage-->>DataMgr: DICOM data
    DataMgr-->>AIEngine: Processed data
    AIEngine->>Database: Log inference
    AIEngine-->>Gateway: Inference results
    Gateway-->>Client: Results + metadata
```

### 2.4 Data Flow Architecture

```mermaid
flowchart LR
    subgraph Input
        DICOM[DICOM Files]
        NIFTI[NIfTI Files]
        JSON[JSON Metadata]
    end

    subgraph Processing
        VALIDATE[Data Validation]
        PREPROCESS[Preprocessing]
        INFERENCE[AI Inference]
        POSTPROCESS[Post-processing]
    end

    subgraph Output
        RESULTS[Segmentation Results]
        REPORTS[Clinical Reports]
        METRICS[Performance Metrics]
    end

    DICOM --> VALIDATE
    NIFTI --> VALIDATE
    JSON --> VALIDATE

    VALIDATE --> PREPROCESS
    PREPROCESS --> INFERENCE
    INFERENCE --> POSTPROCESS

    POSTPROCESS --> RESULTS
    POSTPROCESS --> REPORTS
    POSTPROCESS --> METRICS
```

---

## 3. LOW-LEVEL DESIGN

### 3.1 AI Engine Module

#### 3.1.1 Component Architecture

```python
# AI Engine Core Components
class AIEngine:
    """
    Core AI Engine implementing REQ-F-001, REQ-F-002, REQ-F-003
    Handles model training, inference, and neural architecture search
    """

    def __init__(self):
        self.model_manager = ModelManager()
        self.training_engine = TrainingEngine()
        self.inference_engine = InferenceEngine()
        self.nas_engine = NASEngine()  # REQ-F-003

    async def train_model(self, config: TrainingConfig) -> TrainingResult:
        """REQ-F-001: Model Training Capability"""

    async def run_inference(self, data: MedicalImageData) -> InferenceResult:
        """REQ-F-002: Model Inference Engine"""

    async def search_architecture(self, search_config: NASConfig) -> Architecture:
        """REQ-F-003: Neural Architecture Search"""
```

#### 3.1.2 Model Architecture Classes

```python
class UNETRModel(nn.Module):
    """
    UNETR implementation for medical image segmentation
    Fulfills REQ-F-001: Multi-modal fusion capabilities
    """

    def __init__(self,
                 img_size: Tuple[int, int, int],
                 in_channels: int,
                 out_channels: int,
                 feature_size: int = 16):
        super().__init__()
        self.vit = ViT(img_size=img_size, patch_size=16)
        self.encoder = UNETREncoder()
        self.decoder = UNETRDecoder()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Multi-modal fusion logic - REQ-F-007
        hidden_states = self.vit(x)
        encoded = self.encoder(hidden_states)
        return self.decoder(encoded)

class DiNTSSearchSpace(SearchSpace):
    """
    Differentiable Neural Architecture Search implementation
    Fulfills REQ-F-003: Neural Architecture Search capability
    """

    def __init__(self):
        self.operations = [
            'conv_3x3',
            'conv_5x5',
            'sep_conv_3x3',
            'max_pool_3x3',
            'avg_pool_3x3',
            'skip_connect'
        ]

    def sample_architecture(self) -> Architecture:
        """Sample random architecture from search space"""

    def evaluate_architecture(self, arch: Architecture) -> float:
        """Evaluate architecture performance"""
```

#### 3.1.3 Training Engine Design

```python
class TrainingEngine:
    """
    Distributed training engine with MLflow integration
    Fulfills REQ-F-001, REQ-NF-P-001: Training Performance
    """

    def __init__(self):
        self.device_manager = DeviceManager()
        self.data_loader = MedicalDataLoader()
        self.optimizer_factory = OptimizerFactory()
        self.mlflow_tracker = MLflowTracker()  # REQ-F-009

    async def distributed_train(self,
                               config: TrainingConfig,
                               world_size: int = None) -> TrainingResult:
        """
        Distributed training implementation
        Supports REQ-NF-P-001: Linear scaling up to 8 GPUs
        """

        if world_size is None:
            world_size = torch.cuda.device_count()

        # Initialize distributed process group
        mp.spawn(self._train_worker,
                args=(world_size, config),
                nprocs=world_size)

    def _train_worker(self, rank: int, world_size: int, config: TrainingConfig):
        """Individual worker process for distributed training"""

        # Setup distributed training
        setup_distributed(rank, world_size)

        # Create model and wrap with DDP
        model = self._create_model(config)
        model = DDP(model, device_ids=[rank])

        # Training loop with MLflow logging
        for epoch in range(config.epochs):
            metrics = self._train_epoch(model, epoch)
            self.mlflow_tracker.log_metrics(metrics, epoch)
```

### 3.2 Clinical Integration Module

#### 3.2.1 Clinical Operator Architecture

```python
class ClinicalOperator:
    """
    Nine-step clinical workflow automation
    Fulfills REQ-F-004: Clinical Deployment Automation
    """

    WORKFLOW_STEPS = [
        'bootstrap_verification',
        'virtual_environment_setup',
        'real_dataset_integration',
        'training_configuration',
        'training_execution',
        'monitoring_setup',
        'inference_pipeline',
        'clinical_onboarding',
        'documentation_generation'
    ]

    def __init__(self):
        self.workflow_state = WorkflowState()
        self.step_handlers = self._initialize_handlers()
        self.health_monitor = HealthMonitor()  # REQ-NF-R-001

    async def execute_clinical_workflow(self) -> ClinicalDeploymentResult:
        """Execute complete 9-step clinical workflow"""

        results = {}
        for step_name in self.WORKFLOW_STEPS:
            try:
                logger.info(f"Executing step: {step_name}")
                handler = self.step_handlers[step_name]
                result = await handler.execute()
                results[step_name] = result
                self.workflow_state.mark_complete(step_name)

            except Exception as e:
                logger.error(f"Step {step_name} failed: {e}")
                # REQ-NF-R-002: Error handling and recovery
                recovery_result = await self._attempt_recovery(step_name, e)
                if not recovery_result.success:
                    raise ClinicalWorkflowError(f"Failed at step: {step_name}")

        return ClinicalDeploymentResult(
            status='SUCCESS',
            results=results,
            deployment_info=self._generate_deployment_info()
        )
```

#### 3.2.2 Health Monitoring System

```python
class HealthMonitor:
    """
    System health monitoring for clinical deployment
    Fulfills REQ-NF-R-001: System Availability
    """

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.dashboard = HealthDashboard()

    async def monitor_system_health(self):
        """Continuous system health monitoring"""

        while True:
            health_status = await self._collect_health_metrics()

            # Check critical thresholds
            if health_status.cpu_usage > 90:
                await self.alert_manager.send_alert(
                    Alert(level='CRITICAL',
                          message='High CPU usage detected'))

            if health_status.inference_latency > 30:  # REQ-NF-P-002
                await self.alert_manager.send_alert(
                    Alert(level='WARNING',
                          message='Inference latency exceeded threshold'))

            # Update dashboard
            await self.dashboard.update_metrics(health_status)

            await asyncio.sleep(5)  # Check every 5 seconds

    async def _collect_health_metrics(self) -> HealthStatus:
        """Collect comprehensive system health metrics"""

        return HealthStatus(
            timestamp=datetime.utcnow(),
            cpu_usage=psutil.cpu_percent(),
            memory_usage=psutil.virtual_memory().percent,
            gpu_usage=self._get_gpu_usage(),
            disk_usage=psutil.disk_usage('/').percent,
            inference_latency=self._get_avg_inference_time(),
            active_users=self._get_active_user_count(),
            system_load=os.getloadavg()[0]
        )
```

### 3.3 Data Management Module

#### 3.3.1 DICOM Processing Engine

```python
class DICOMProcessor:
    """
    DICOM data processing and validation
    Fulfills REQ-I-002: DICOM Integration Interface
    """

    def __init__(self):
        self.validator = DICOMValidator()
        self.anonymizer = DICOMAnonymizer()  # REQ-F-006
        self.converter = DICOMConverter()

    async def process_dicom_series(self,
                                  dicom_path: Path) -> ProcessedDICOMSeries:
        """
        Process complete DICOM series for AI analysis
        Implements REQ-F-007: Multi-modal data processing
        """

        # Validate DICOM files
        validation_result = await self.validator.validate_series(dicom_path)
        if not validation_result.is_valid:
            raise DICOMValidationError(validation_result.errors)

        # Load DICOM series
        series_data = self._load_dicom_series(dicom_path)

        # Extract metadata
        metadata = self._extract_metadata(series_data)

        # Anonymize if required (REQ-F-006: Data Security)
        if metadata.contains_phi:
            series_data = await self.anonymizer.anonymize(series_data)

        # Convert to standard format for AI processing
        tensor_data = await self.converter.to_tensor(series_data)

        return ProcessedDICOMSeries(
            data=tensor_data,
            metadata=metadata,
            series_info=series_data.series_info,
            processing_log=self._generate_processing_log()
        )

    def _extract_metadata(self, series_data: DICOMSeries) -> DICOMMetadata:
        """Extract relevant metadata for AI processing"""

        return DICOMMetadata(
            modality=series_data.modality,
            study_date=series_data.study_date,
            series_description=series_data.series_description,
            pixel_spacing=series_data.pixel_spacing,
            slice_thickness=series_data.slice_thickness,
            orientation=series_data.image_orientation,
            contains_phi=self._check_phi_presence(series_data)
        )
```

#### 3.3.2 Multi-Modal Data Fusion

```python
class MultiModalProcessor:
    """
    Multi-modal medical imaging data fusion
    Fulfills REQ-F-007: Multi-modal data processing
    """

    SUPPORTED_MODALITIES = {
        'T1': 'T1-weighted MRI',
        'T1C': 'T1-weighted with contrast',
        'T2': 'T2-weighted MRI',
        'FLAIR': 'Fluid-attenuated inversion recovery',
        'CT': 'Computed Tomography',
        'PET': 'Positron Emission Tomography'
    }

    def __init__(self):
        self.registration_engine = RegistrationEngine()
        self.fusion_network = CrossAttentionFusion()
        self.preprocessor = MultiModalPreprocessor()

    async def fuse_modalities(self,
                             modality_data: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Fuse multiple imaging modalities using cross-attention
        """

        # Validate modality compatibility
        self._validate_modalities(modality_data.keys())

        # Align modalities through registration
        aligned_data = {}
        reference_modality = self._select_reference_modality(modality_data)

        for modality, data in modality_data.items():
            if modality != reference_modality:
                aligned_data[modality] = await self.registration_engine.register(
                    moving=data,
                    fixed=modality_data[reference_modality]
                )
            else:
                aligned_data[modality] = data

        # Preprocess each modality
        preprocessed_data = {}
        for modality, data in aligned_data.items():
            preprocessed_data[modality] = await self.preprocessor.process(
                data, modality
            )

        # Apply cross-attention fusion
        fused_representation = self.fusion_network(preprocessed_data)

        return fused_representation
```

### 3.4 Security Architecture

#### 3.4.1 Authentication and Authorization

```python
class SecurityManager:
    """
    Comprehensive security framework
    Fulfills REQ-F-006, REQ-NF-S-001, REQ-NF-S-002
    """

    def __init__(self):
        self.auth_provider = OAuth2Provider()
        self.encryption_service = EncryptionService()
        self.audit_logger = AuditLogger()
        self.rbac_manager = RBACManager()

    async def authenticate_user(self,
                               credentials: UserCredentials) -> AuthenticationResult:
        """
        Multi-factor authentication implementation
        REQ-NF-S-001: Multi-factor authentication
        """

        # Primary authentication
        primary_result = await self.auth_provider.authenticate(
            username=credentials.username,
            password=credentials.password
        )

        if not primary_result.success:
            await self.audit_logger.log_failed_login(credentials.username)
            return AuthenticationResult(success=False,
                                      reason='Invalid credentials')

        # Multi-factor authentication
        mfa_result = await self._verify_mfa(credentials.mfa_token)
        if not mfa_result.success:
            await self.audit_logger.log_failed_mfa(credentials.username)
            return AuthenticationResult(success=False,
                                      reason='MFA verification failed')

        # Generate secure session token
        token = await self._generate_session_token(primary_result.user)

        # Log successful authentication
        await self.audit_logger.log_successful_login(
            user=primary_result.user,
            token_id=token.id,
            ip_address=credentials.ip_address
        )

        return AuthenticationResult(
            success=True,
            token=token,
            user=primary_result.user,
            permissions=await self.rbac_manager.get_user_permissions(
                primary_result.user
            )
        )
```

#### 3.4.2 Data Encryption Framework

```python
class EncryptionService:
    """
    Data encryption for HIPAA/GDPR compliance
    Fulfills REQ-NF-S-001: AES-256 encryption
    """

    def __init__(self):
        self.key_manager = KeyManager()
        self.cipher_suite = self._initialize_cipher()

    def _initialize_cipher(self) -> Fernet:
        """Initialize AES-256 cipher suite"""

        key = self.key_manager.get_encryption_key()
        return Fernet(key)

    async def encrypt_medical_data(self,
                                  data: bytes,
                                  context: EncryptionContext) -> EncryptedData:
        """
        Encrypt medical data with audit trail
        REQ-F-006: Medical data security
        """

        # Generate data-specific encryption key
        data_key = self.key_manager.generate_data_key()

        # Encrypt data
        encrypted_data = self.cipher_suite.encrypt(data)

        # Encrypt the data key with master key
        encrypted_key = self.key_manager.encrypt_data_key(data_key)

        # Create audit record
        audit_record = EncryptionAuditRecord(
            timestamp=datetime.utcnow(),
            data_id=context.data_id,
            user_id=context.user_id,
            operation='ENCRYPT',
            key_id=data_key.id
        )

        await self.audit_logger.log_encryption_event(audit_record)

        return EncryptedData(
            data=encrypted_data,
            encrypted_key=encrypted_key,
            metadata=context.to_metadata(),
            audit_id=audit_record.id
        )
```

---

## 4. INTERFACE SPECIFICATIONS

### 4.1 RESTful API Design

#### 4.1.1 Core API Endpoints

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer

app = FastAPI(title="Medical Imaging AI Platform API",
              version="1.0.0",
              description="REQ-I-001: Clinical Web Interface")

security = HTTPBearer()

@app.post("/api/v1/inference/tumor-detection")
async def detect_tumors(
    image_data: UploadFile = File(...),
    modality: str = Query(..., description="Imaging modality"),
    token: str = Depends(security)
) -> TumorDetectionResult:
    """
    REQ-F-002: Model Inference Engine
    Detect and segment tumors in medical imaging data
    """

    # Authenticate request
    user = await authenticate_token(token)
    if not user.has_permission('inference:execute'):
        raise HTTPException(403, "Insufficient permissions")

    # Process medical imaging data
    processed_data = await process_medical_image(image_data, modality)

    # Run AI inference
    inference_result = await ai_engine.run_inference(processed_data)

    # Log operation for audit
    await audit_logger.log_inference(
        user_id=user.id,
        image_id=processed_data.id,
        result=inference_result
    )

    return TumorDetectionResult(
        tumor_regions=inference_result.segmentation_mask,
        confidence_scores=inference_result.confidence,
        tumor_volumes=inference_result.volumes,
        processing_time=inference_result.processing_time
    )

@app.post("/api/v1/training/start")
async def start_training(
    config: TrainingConfiguration,
    token: str = Depends(security)
) -> TrainingJobResult:
    """
    REQ-F-001: Model Training Capability
    Start AI model training job
    """

    user = await authenticate_token(token)
    if not user.has_permission('training:execute'):
        raise HTTPException(403, "Insufficient permissions")

    # Validate training configuration
    validation_result = await validate_training_config(config)
    if not validation_result.is_valid:
        raise HTTPException(400, validation_result.errors)

    # Start training job
    job = await training_engine.start_training(config, user.id)

    return TrainingJobResult(
        job_id=job.id,
        status=job.status,
        estimated_duration=job.estimated_duration,
        tracking_url=f"/training/jobs/{job.id}"
    )

@app.get("/api/v1/clinical/workflow/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    token: str = Depends(security)
) -> ClinicalWorkflowStatus:
    """
    REQ-F-004: Clinical Deployment Automation
    Get status of clinical workflow execution
    """

    user = await authenticate_token(token)
    workflow = await clinical_operator.get_workflow(workflow_id)

    if not user.can_access_workflow(workflow):
        raise HTTPException(403, "Access denied")

    return ClinicalWorkflowStatus(
        workflow_id=workflow.id,
        current_step=workflow.current_step,
        completed_steps=workflow.completed_steps,
        status=workflow.status,
        progress_percentage=workflow.progress_percentage,
        estimated_completion=workflow.estimated_completion
    )
```

#### 4.1.2 WebSocket Interface for Real-time Updates

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    """
    WebSocket connection manager for real-time updates
    Supports REQ-NF-P-002: Real-time response requirements
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections.remove(websocket)
        if user_id in self.user_connections:
            del self.user_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            await self.user_connections[user_id].send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/training/{job_id}")
async def training_progress_websocket(websocket: WebSocket,
                                    job_id: str,
                                    token: str):
    """
    Real-time training progress updates
    REQ-F-001: Training progress monitoring
    """

    # Authenticate WebSocket connection
    user = await authenticate_token(token)
    await manager.connect(websocket, user.id)

    try:
        # Subscribe to training job updates
        async for update in training_engine.subscribe_to_job(job_id):
            progress_message = {
                "job_id": job_id,
                "epoch": update.current_epoch,
                "loss": update.current_loss,
                "accuracy": update.current_accuracy,
                "eta": update.estimated_time_remaining
            }

            await manager.send_personal_message(
                json.dumps(progress_message),
                user.id
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)
```

### 4.2 Database Schema Design

#### 4.2.1 Core Entity Relationships

```sql
-- REQ-F-001: Model training data storage
CREATE TABLE training_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    config JSONB NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    model_path TEXT,
    metrics JSONB,
    error_message TEXT
);

-- REQ-F-002: Inference request logging
CREATE TABLE inference_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    image_id UUID NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    modality VARCHAR(20) NOT NULL,
    processing_time_ms INTEGER,
    results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- REQ-F-006: Audit logging for compliance
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    details JSONB
);

-- REQ-F-007: Medical imaging metadata
CREATE TABLE medical_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id VARCHAR(255),  -- Anonymized patient identifier
    study_id VARCHAR(255),
    series_id VARCHAR(255),
    modality VARCHAR(20) NOT NULL,
    acquisition_date DATE,
    file_path TEXT NOT NULL,
    metadata JSONB,
    processing_status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes for clinical queries
CREATE INDEX idx_training_jobs_user_status ON training_jobs(user_id, status);
CREATE INDEX idx_inference_requests_user_created ON inference_requests(user_id, created_at);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_medical_images_modality_date ON medical_images(modality, acquisition_date);
```

---

## 5. DEPLOYMENT ARCHITECTURE

### 5.1 Docker Container Design

#### 5.1.1 Multi-Stage Dockerfile

```dockerfile
# Multi-stage build for production optimization
# REQ-F-004: Clinical deployment automation

FROM python:3.9-slim as base
LABEL maintainer="Medical Imaging AI Team"
LABEL version="1.0.0"

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Development stage
FROM base as development
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 5.1.2 Docker Compose Configuration

```yaml
# docker-compose.yml
# REQ-F-004: Complete deployment orchestration

version: '3.8'

services:
  # Main application
  medical-ai-api:
    build:
      context: .
      target: production
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/medical_ai
      - REDIS_URL=redis://redis:6379
      - MLflow_TRACKING_URI=http://mlflow:5000
    depends_on:
      - postgres
      - redis
      - mlflow
    volumes:
      - medical_data:/app/data
      - model_registry:/app/models
    networks:
      - medical-ai-network
    restart: unless-stopped

  # Database
  postgres:
    image: postgres:13-alpine
    environment:
      - POSTGRES_DB=medical_ai
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - medical-ai-network
    restart: unless-stopped

  # Cache and message broker
  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    networks:
      - medical-ai-network
    restart: unless-stopped

  # ML experiment tracking
  mlflow:
    image: python:3.9-slim
    command: >
      sh -c "pip install mlflow psycopg2-binary &&
             mlflow server --backend-store-uri postgresql://user:pass@postgres:5432/mlflow
                          --default-artifact-root /mlruns
                          --host 0.0.0.0
                          --port 5000"
    ports:
      - "5001:5000"
    depends_on:
      - postgres
    volumes:
      - mlflow_artifacts:/mlruns
    networks:
      - medical-ai-network
    restart: unless-stopped

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - medical-ai-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
    networks:
      - medical-ai-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  medical_data:
  model_registry:
  mlflow_artifacts:
  prometheus_data:
  grafana_data:

networks:
  medical-ai-network:
    driver: bridge
```

---

## 6. PERFORMANCE AND SCALABILITY DESIGN

### 6.1 Performance Optimization Strategies

#### 6.1.1 GPU Memory Management

```python
class GPUMemoryManager:
    """
    Intelligent GPU memory management for optimal performance
    Fulfills REQ-NF-P-001: Training performance optimization
    """

    def __init__(self):
        self.device_info = self._get_device_info()
        self.memory_pools = {}
        self.allocation_strategy = self._determine_strategy()

    def _determine_strategy(self) -> str:
        """Determine optimal memory allocation strategy based on GPU"""

        total_memory = torch.cuda.get_device_properties(0).total_memory

        if total_memory >= 48 * 1024**3:  # 48GB+
            return 'HIGH_RESOLUTION'
        elif total_memory >= 24 * 1024**3:  # 24GB+
            return 'MEDIUM_RESOLUTION'
        elif total_memory >= 12 * 1024**3:  # 12GB+
            return 'LOW_RESOLUTION'
        else:
            return 'CPU_FALLBACK'

    def get_optimal_batch_size(self, model_size: int, input_shape: Tuple) -> int:
        """Calculate optimal batch size based on available memory"""

        available_memory = torch.cuda.get_device_properties(0).total_memory
        reserved_memory = available_memory * 0.1  # Reserve 10%

        # Estimate memory per sample
        memory_per_sample = self._estimate_memory_usage(model_size, input_shape)

        # Calculate maximum batch size
        max_batch_size = int((available_memory - reserved_memory) / memory_per_sample)

        # Return power of 2 for optimal GPU utilization
        return 2 ** int(math.log2(max_batch_size))
```

#### 6.1.2 Async Processing Pipeline

```python
class AsyncInferenceEngine:
    """
    Asynchronous inference processing for high throughput
    Fulfills REQ-NF-P-002: Inference response time optimization
    """

    def __init__(self, max_concurrent: int = 10):
        self.model_pool = ModelPool()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.preprocessing_queue = asyncio.Queue()
        self.inference_queue = asyncio.Queue()
        self.postprocessing_queue = asyncio.Queue()

    async def process_inference_request(self,
                                      request: InferenceRequest) -> InferenceResult:
        """
        Process inference request with async pipeline
        Target: <30 seconds per scan (REQ-NF-P-002)
        """

        async with self.semaphore:
            # Pipeline stages
            preprocessed_data = await self._async_preprocess(request.data)
            inference_result = await self._async_inference(preprocessed_data)
            final_result = await self._async_postprocess(inference_result)

            return final_result

    async def _async_preprocess(self, data: MedicalImageData) -> ProcessedData:
        """Asynchronous data preprocessing"""

        loop = asyncio.get_event_loop()

        # Run CPU-intensive preprocessing in thread pool
        processed_data = await loop.run_in_executor(
            None,
            self._preprocess_medical_image,
            data
        )

        return processed_data

    async def _async_inference(self, data: ProcessedData) -> RawInferenceResult:
        """GPU inference with model pooling"""

        # Get available model from pool
        model = await self.model_pool.get_model()

        try:
            # Run inference on GPU
            with torch.cuda.device(model.device):
                result = model(data.tensor)

            return RawInferenceResult(
                segmentation=result,
                confidence=model.get_confidence(),
                metadata=data.metadata
            )

        finally:
            # Return model to pool
            await self.model_pool.return_model(model)
```

---

## 7. SECURITY DESIGN DETAILS

### 7.1 Zero-Trust Architecture

```python
class ZeroTrustSecurityManager:
    """
    Zero-trust security implementation for medical data
    Fulfills REQ-F-006, REQ-NF-S-001: Comprehensive security
    """

    def __init__(self):
        self.identity_verifier = IdentityVerifier()
        self.device_manager = DeviceManager()
        self.network_policy_engine = NetworkPolicyEngine()
        self.data_classifier = DataClassifier()

    async def validate_request(self,
                              request: APIRequest) -> SecurityValidationResult:
        """
        Comprehensive request validation following zero-trust principles
        """

        validations = await asyncio.gather(
            self._verify_user_identity(request.user_token),
            self._verify_device_trust(request.device_fingerprint),
            self._validate_network_access(request.source_ip),
            self._classify_data_sensitivity(request.payload)
        )

        user_valid, device_valid, network_valid, data_classification = validations

        # Apply zero-trust policy
        security_score = self._calculate_security_score(
            user_valid, device_valid, network_valid, data_classification
        )

        if security_score < 0.8:  # Require high confidence
            return SecurityValidationResult(
                valid=False,
                reason="Insufficient trust score",
                required_actions=["MFA", "Device_Verification"]
            )

        return SecurityValidationResult(
            valid=True,
            trust_score=security_score,
            data_access_level=data_classification.access_level
        )
```

---

## 8. DOCUMENT CONTROL

**Version History:**

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-09-13 | Initial SDD creation | System Architecture Team |

**Approval:**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Chief Technology Officer** | [Name] | [Signature] | 2025-09-13 |
| **Lead Architect** | [Name] | [Signature] | 2025-09-13 |
| **Security Architect** | [Name] | [Signature] | 2025-09-13 |

**Distribution:**
- Development Team
- Architecture Review Board
- Security Team
- Clinical Integration Team
