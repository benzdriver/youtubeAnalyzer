import pytest
import docker
import requests
import time
import subprocess
import os


class TestDockerIntegration:
    """Test suite for Docker container integration."""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker client fixture."""
        return docker.from_env()
    
    @pytest.fixture(scope="class")
    def compose_project_name(self):
        """Docker Compose project name."""
        return "youtubeanalyzer"
    
    def test_docker_compose_file_exists(self):
        """Test that docker-compose.yml exists and is valid."""
        compose_file = "/home/ubuntu/repos/youtubeAnalyzer/docker-compose.yml"
        assert os.path.exists(compose_file), "docker-compose.yml file not found"
        
        import yaml
        with open(compose_file, 'r') as f:
            try:
                compose_config = yaml.safe_load(f)
                assert "services" in compose_config
                assert "version" in compose_config or "services" in compose_config
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid docker-compose.yml: {str(e)}")
    
    def test_dockerfile_exists(self):
        """Test that Dockerfiles exist for backend and frontend."""
        backend_dockerfile = "/home/ubuntu/repos/youtubeAnalyzer/backend/Dockerfile"
        frontend_dockerfile = "/home/ubuntu/repos/youtubeAnalyzer/frontend/Dockerfile"
        
        assert os.path.exists(backend_dockerfile), "Backend Dockerfile not found"
        assert os.path.exists(frontend_dockerfile), "Frontend Dockerfile not found"
    
    def test_docker_compose_services_defined(self):
        """Test that required services are defined in docker-compose.yml."""
        import yaml
        
        compose_file = "/home/ubuntu/repos/youtubeAnalyzer/docker-compose.yml"
        with open(compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)
        
        services = compose_config.get("services", {})
        required_services = ["backend", "frontend", "postgres", "redis"]
        
        for service in required_services:
            assert service in services, f"Service '{service}' not defined in docker-compose.yml"
    
    def test_docker_compose_up(self):
        """Test that docker-compose up starts all services."""
        compose_dir = "/home/ubuntu/repos/youtubeAnalyzer"
        
        try:
            result = subprocess.run(
                ["docker", "compose", "up", "-d", "--build"],
                cwd=compose_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode != 0:
                pytest.fail(f"docker-compose up failed: {result.stderr}")
            
            time.sleep(30)
            
            result = subprocess.run(
                ["docker", "compose", "ps"],
                cwd=compose_dir,
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "Up" in result.stdout or "running" in result.stdout
            
        except subprocess.TimeoutExpired:
            pytest.fail("docker-compose up timed out after 5 minutes")
        except Exception as e:
            pytest.fail(f"docker-compose up failed: {str(e)}")
    
    def test_container_health_checks(self, docker_client):
        """Test container health checks."""
        containers = docker_client.containers.list(
            filters={"label": "com.docker.compose.project=youtubeanalyzer"}
        )
        
        assert len(containers) > 0, "No containers found for the project"
        
        for container in containers:
            container.reload()
            assert container.status == "running", f"Container {container.name} is not running"
            
            if container.attrs.get("Config", {}).get("Healthcheck"):
                health = container.attrs.get("State", {}).get("Health", {})
                if health:
                    assert health.get("Status") == "healthy", f"Container {container.name} is not healthy"
    
    def test_service_discovery(self):
        """Test that services can discover each other."""
        compose_dir = "/home/ubuntu/repos/youtubeAnalyzer"
        
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "backend", "python", "-c", 
             "from app.core.database import engine; import asyncio; asyncio.run(engine.dispose())"],
            cwd=compose_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0 and "connection" in result.stderr.lower():
            pytest.fail(f"Backend cannot connect to database: {result.stderr}")
    
    def test_network_connectivity(self):
        """Test network connectivity between containers."""
        compose_dir = "/home/ubuntu/repos/youtubeAnalyzer"
        
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "backend", "python", "-c",
             "import redis; r = redis.from_url('redis://redis:6379'); r.ping()"],
            cwd=compose_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            pytest.fail(f"Backend cannot connect to Redis: {result.stderr}")
    
    def test_port_exposure(self):
        """Test that services expose correct ports."""
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            assert response.status_code == 200
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Backend port 8000 not accessible: {str(e)}")
        
        try:
            response = requests.get("http://localhost:3000", timeout=10)
            assert response.status_code == 200
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Frontend port 3000 not accessible: {str(e)}")
    
    def test_volume_mounts(self, docker_client):
        """Test that volumes are properly mounted."""
        containers = docker_client.containers.list(
            filters={"label": "com.docker.compose.project=youtubeanalyzer"}
        )
        
        for container in containers:
            mounts = container.attrs.get("Mounts", [])
            
            if "backend" in container.name:
                code_mounts = [m for m in mounts if "/app" in m.get("Destination", "")]
                assert len(code_mounts) > 0, f"Backend container {container.name} missing code mount"
    
    def test_environment_variables_in_containers(self):
        """Test that environment variables are properly passed to containers."""
        compose_dir = "/home/ubuntu/repos/youtubeAnalyzer"
        
        result = subprocess.run(
            ["docker", "compose", "exec", "-T", "backend", "python", "-c",
             "import os; print(os.getenv('DATABASE_URL', 'NOT_SET'))"],
            cwd=compose_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            assert "NOT_SET" not in result.stdout, "DATABASE_URL not set in backend container"
            assert "postgresql" in result.stdout, "DATABASE_URL should contain postgresql"
    
    def test_container_startup_time(self):
        """Test that containers start within acceptable time."""
        compose_dir = "/home/ubuntu/repos/youtubeAnalyzer"
        
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=compose_dir,
            capture_output=True,
            text=True
        )
        
        start_time = time.time()
        
        result = subprocess.run(
            ["docker", "compose", "up", "-d"],
            cwd=compose_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        end_time = time.time()
        startup_time = end_time - start_time
        
        assert result.returncode == 0, f"Container startup failed: {result.stderr}"
        assert startup_time < 30, f"Container startup time {startup_time}s exceeds 30s requirement"
    
    def test_docker_compose_down(self):
        """Test that docker-compose down stops all services cleanly."""
        compose_dir = "/home/ubuntu/repos/youtubeAnalyzer"
        
        result = subprocess.run(
            ["docker", "compose", "down"],
            cwd=compose_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"docker-compose down failed: {result.stderr}"
        
        result = subprocess.run(
            ["docker", "compose", "ps"],
            cwd=compose_dir,
            capture_output=True,
            text=True
        )
        
        assert "Up" not in result.stdout, "Some containers are still running after docker-compose down"
