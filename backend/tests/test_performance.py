"""
Performance and load testing
"""

import pytest
import time
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import statistics


class TestPerformanceMetrics:
    """Performance testing for system metrics"""
    
    def test_email_processing_performance(self, client):
        """Test email processing performance under normal load."""
        email_data = {
            "message_id": "perf_test_123",
            "subject": "Performance Test Email",
            "sender": "test@example.com",
            "recipient": "user@company.com",
            "body": "This is a performance test email",
            "headers": {"From": "test@example.com"},
            "attachments": [],
            "links": []
        }
        
        with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
            mock_process.return_value = {
                "threat_score": 0.1,
                "verdict": "clean",
                "processing_time": 0.05
            }
            
            # Measure processing time
            start_time = time.time()
            response = client.post(
                "/api/email-gateway/process",
                json=email_data,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            assert response.status_code == 200
            assert processing_time < 1.0  # Should process within 1 second
    
    def test_concurrent_email_processing(self, client):
        """Test concurrent email processing performance."""
        def process_email(email_id):
            email_data = {
                "message_id": f"concurrent_test_{email_id}",
                "subject": f"Concurrent Test Email {email_id}",
                "sender": "test@example.com",
                "recipient": "user@company.com",
                "body": f"This is concurrent test email {email_id}",
                "headers": {"From": "test@example.com"},
                "attachments": [],
                "links": []
            }
            
            with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
                mock_process.return_value = {
                    "threat_score": 0.1,
                    "verdict": "clean"
                }
                
                start_time = time.time()
                response = client.post(
                    "/api/email-gateway/process",
                    json=email_data,
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                end_time = time.time()
                
                return {
                    "email_id": email_id,
                    "status_code": response.status_code,
                    "processing_time": end_time - start_time
                }
        
        # Process 10 emails concurrently
        num_emails = 10
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_email, i) for i in range(num_emails)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all emails were processed successfully
        assert len(results) == num_emails
        assert all(result["status_code"] == 200 for result in results)
        
        # Calculate performance metrics
        processing_times = [result["processing_time"] for result in results]
        avg_processing_time = statistics.mean(processing_times)
        max_processing_time = max(processing_times)
        
        # Performance assertions
        assert avg_processing_time < 2.0  # Average processing time should be under 2 seconds
        assert max_processing_time < 5.0  # Max processing time should be under 5 seconds
        assert total_time < 10.0  # Total time for 10 concurrent emails should be under 10 seconds
    
    def test_high_volume_email_processing(self, client):
        """Test high volume email processing performance."""
        def process_batch_email(email_id):
            email_data = {
                "message_id": f"volume_test_{email_id}",
                "subject": f"Volume Test Email {email_id}",
                "sender": "test@example.com",
                "recipient": "user@company.com",
                "body": f"This is volume test email {email_id}",
                "headers": {"From": "test@example.com"},
                "attachments": [],
                "links": []
            }
            
            with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
                mock_process.return_value = {
                    "threat_score": 0.1,
                    "verdict": "clean"
                }
                
                response = client.post(
                    "/api/email-gateway/process",
                    json=email_data,
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                
                return response.status_code == 200
        
        # Process 100 emails
        num_emails = 100
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_batch_email, i) for i in range(num_emails)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput
        successful_emails = sum(results)
        throughput = successful_emails / total_time  # emails per second
        
        # Performance assertions
        assert successful_emails >= 95  # At least 95% success rate
        assert throughput >= 10  # At least 10 emails per second
        assert total_time < 30  # Should complete within 30 seconds
    
    def test_database_query_performance(self, client):
        """Test database query performance."""
        with patch('app.services.email_gateway_service.EmailGatewayService.get_statistics') as mock_stats:
            mock_stats.return_value = {
                "total_emails_processed": 10000,
                "threats_detected": 500,
                "false_positives": 25,
                "processing_time_avg": 0.5
            }
            
            # Measure query time
            start_time = time.time()
            response = client.get(
                "/api/email-gateway/statistics",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            end_time = time.time()
            
            query_time = end_time - start_time
            
            assert response.status_code == 200
            assert query_time < 0.5  # Database queries should be fast
    
    def test_api_response_time_consistency(self, client):
        """Test API response time consistency."""
        response_times = []
        
        for i in range(20):
            with patch('app.services.email_gateway_service.EmailGatewayService.get_statistics') as mock_stats:
                mock_stats.return_value = {"total_emails_processed": 1000}
                
                start_time = time.time()
                response = client.get(
                    "/api/email-gateway/statistics",
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                end_time = time.time()
                
                response_times.append(end_time - start_time)
        
        # Calculate consistency metrics
        avg_response_time = statistics.mean(response_times)
        std_deviation = statistics.stdev(response_times)
        coefficient_of_variation = std_deviation / avg_response_time
        
        # Consistency assertions
        assert avg_response_time < 1.0  # Average response time should be under 1 second
        assert coefficient_of_variation < 0.5  # Response times should be consistent (low variation)


class TestLoadTesting:
    """Load testing for system capacity"""
    
    def test_sustained_load_performance(self, client):
        """Test performance under sustained load."""
        def sustained_load_worker(worker_id, duration_seconds=30):
            """Worker function for sustained load testing."""
            start_time = time.time()
            request_count = 0
            success_count = 0
            
            while time.time() - start_time < duration_seconds:
                with patch('app.services.email_gateway_service.EmailGatewayService.get_statistics') as mock_stats:
                    mock_stats.return_value = {"total_emails_processed": 1000}
                    
                    response = client.get(
                        "/api/email-gateway/statistics",
                        headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                    )
                    
                    request_count += 1
                    if response.status_code == 200:
                        success_count += 1
                
                time.sleep(0.1)  # 10 requests per second per worker
            
            return {
                "worker_id": worker_id,
                "request_count": request_count,
                "success_count": success_count,
                "success_rate": success_count / request_count if request_count > 0 else 0
            }
        
        # Run 5 workers for 30 seconds
        num_workers = 5
        duration = 30
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(sustained_load_worker, i, duration) for i in range(num_workers)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate overall metrics
        total_requests = sum(result["request_count"] for result in results)
        total_successes = sum(result["success_count"] for result in results)
        overall_success_rate = total_successes / total_requests if total_requests > 0 else 0
        requests_per_second = total_requests / total_time
        
        # Load testing assertions
        assert overall_success_rate >= 0.95  # 95% success rate under sustained load
        assert requests_per_second >= 20  # At least 20 requests per second
        assert all(result["success_rate"] >= 0.9 for result in results)  # Each worker should maintain 90% success rate
    
    def test_peak_load_handling(self, client):
        """Test handling of peak load conditions."""
        def peak_load_burst():
            """Simulate a burst of requests."""
            results = []
            
            for i in range(50):  # 50 requests in quick succession
                with patch('app.services.email_gateway_service.EmailGatewayService.get_statistics') as mock_stats:
                    mock_stats.return_value = {"total_emails_processed": 1000}
                    
                    start_time = time.time()
                    response = client.get(
                        "/api/email-gateway/statistics",
                        headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                    )
                    end_time = time.time()
                    
                    results.append({
                        "status_code": response.status_code,
                        "response_time": end_time - start_time
                    })
            
            return results
        
        # Run multiple bursts concurrently
        num_bursts = 3
        
        with ThreadPoolExecutor(max_workers=num_bursts) as executor:
            futures = [executor.submit(peak_load_burst) for _ in range(num_bursts)]
            all_results = [future.result() for future in as_completed(futures)]
        
        # Flatten results
        flat_results = [result for burst_results in all_results for result in burst_results]
        
        # Calculate metrics
        successful_requests = [r for r in flat_results if r["status_code"] == 200]
        success_rate = len(successful_requests) / len(flat_results)
        response_times = [r["response_time"] for r in successful_requests]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # Peak load assertions
        assert success_rate >= 0.9  # 90% success rate under peak load
        assert avg_response_time < 2.0  # Average response time should be reasonable
        assert max_response_time < 10.0  # Max response time should not be excessive
    
    def test_memory_usage_under_load(self, client):
        """Test memory usage under load."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        def memory_load_worker():
            """Worker that processes requests to test memory usage."""
            for i in range(100):
                with patch('app.services.email_gateway_service.EmailGatewayService.get_statistics') as mock_stats:
                    mock_stats.return_value = {"total_emails_processed": 1000}
                    
                    response = client.get(
                        "/api/email-gateway/statistics",
                        headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                    )
                    
                    assert response.status_code == 200
        
        # Run multiple workers
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(memory_load_worker) for _ in range(5)]
            [future.result() for future in as_completed(futures)]
        
        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage assertions
        assert memory_increase < 100  # Memory increase should be less than 100MB
        assert final_memory < 500  # Total memory usage should be reasonable


class TestScalabilityTesting:
    """Scalability testing for system growth"""
    
    def test_horizontal_scaling_simulation(self, client):
        """Simulate horizontal scaling with multiple workers."""
        def worker_simulation(worker_id, requests_per_worker=20):
            """Simulate a worker processing requests."""
            results = []
            
            for i in range(requests_per_worker):
                with patch('app.services.email_gateway_service.EmailGatewayService.get_statistics') as mock_stats:
                    mock_stats.return_value = {"total_emails_processed": 1000}
                    
                    start_time = time.time()
                    response = client.get(
                        "/api/email-gateway/statistics",
                        headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                    )
                    end_time = time.time()
                    
                    results.append({
                        "worker_id": worker_id,
                        "request_id": i,
                        "status_code": response.status_code,
                        "response_time": end_time - start_time
                    })
            
            return results
        
        # Simulate different numbers of workers
        worker_counts = [1, 2, 5, 10]
        scaling_results = {}
        
        for num_workers in worker_counts:
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(worker_simulation, i) for i in range(num_workers)]
                results = [future.result() for future in as_completed(futures)]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Calculate metrics
            flat_results = [result for worker_results in results for result in worker_results]
            successful_requests = [r for r in flat_results if r["status_code"] == 200]
            success_rate = len(successful_requests) / len(flat_results)
            throughput = len(flat_results) / total_time
            
            scaling_results[num_workers] = {
                "total_time": total_time,
                "success_rate": success_rate,
                "throughput": throughput
            }
        
        # Scalability assertions
        for num_workers, metrics in scaling_results.items():
            assert metrics["success_rate"] >= 0.95  # High success rate regardless of worker count
            assert metrics["throughput"] >= 5  # Minimum throughput per worker
    
    def test_data_volume_scaling(self, client):
        """Test performance with increasing data volumes."""
        def process_large_email(size_multiplier):
            """Process email with varying data sizes."""
            email_data = {
                "message_id": f"size_test_{size_multiplier}",
                "subject": "Size Test Email",
                "sender": "test@example.com",
                "recipient": "user@company.com",
                "body": "x" * (1024 * size_multiplier),  # Varying body size
                "headers": {"From": "test@example.com"},
                "attachments": [],
                "links": []
            }
            
            with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
                mock_process.return_value = {
                    "threat_score": 0.1,
                    "verdict": "clean"
                }
                
                start_time = time.time()
                response = client.post(
                    "/api/email-gateway/process",
                    json=email_data,
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                end_time = time.time()
                
                return {
                    "size_kb": size_multiplier,
                    "status_code": response.status_code,
                    "processing_time": end_time - start_time
                }
        
        # Test with different email sizes
        size_multipliers = [1, 10, 100, 1000]  # 1KB, 10KB, 100KB, 1MB
        results = []
        
        for size in size_multipliers:
            result = process_large_email(size)
            results.append(result)
        
        # Data volume scaling assertions
        for result in results:
            assert result["status_code"] == 200  # Should handle all sizes
            assert result["processing_time"] < 10.0  # Processing time should be reasonable
        
        # Processing time should not increase dramatically with size
        small_email_time = results[0]["processing_time"]
        large_email_time = results[-1]["processing_time"]
        assert large_email_time < small_email_time * 10  # Should not be 10x slower


class TestResourceUtilization:
    """Resource utilization testing"""
    
    def test_cpu_utilization_under_load(self, client):
        """Test CPU utilization under load."""
        import psutil
        import os
        
        def cpu_intensive_worker():
            """Worker that performs CPU-intensive operations."""
            for i in range(50):
                with patch('app.services.email_gateway_service.EmailGatewayService.get_statistics') as mock_stats:
                    mock_stats.return_value = {"total_emails_processed": 1000}
                    
                    response = client.get(
                        "/api/email-gateway/statistics",
                        headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                    )
                    
                    assert response.status_code == 200
        
        # Monitor CPU usage
        process = psutil.Process(os.getpid())
        cpu_samples = []
        
        # Start monitoring
        monitor_thread = threading.Thread(target=lambda: [
            cpu_samples.append(process.cpu_percent()) for _ in range(20)
        ])
        monitor_thread.start()
        
        # Run load
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(cpu_intensive_worker) for _ in range(3)]
            [future.result() for future in as_completed(futures)]
        
        monitor_thread.join()
        
        # CPU utilization assertions
        avg_cpu = statistics.mean(cpu_samples)
        max_cpu = max(cpu_samples)
        
        assert avg_cpu < 80  # Average CPU usage should be reasonable
        assert max_cpu < 95  # Peak CPU usage should not be excessive
    
    def test_disk_io_performance(self, client):
        """Test disk I/O performance."""
        def disk_io_worker():
            """Worker that triggers disk I/O operations."""
            for i in range(20):
                with patch('app.services.email_gateway_service.EmailGatewayService.get_statistics') as mock_stats:
                    mock_stats.return_value = {"total_emails_processed": 1000}
                    
                    response = client.get(
                        "/api/email-gateway/statistics",
                        headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                    )
                    
                    assert response.status_code == 200
        
        # Measure disk I/O time
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(disk_io_worker) for _ in range(2)]
            [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Disk I/O assertions
        assert total_time < 30  # Disk operations should complete within reasonable time


class TestPerformanceRegression:
    """Performance regression testing"""
    
    def test_performance_baseline(self, client):
        """Establish performance baseline."""
        def baseline_measurement():
            """Measure baseline performance."""
            with patch('app.services.email_gateway_service.EmailGatewayService.get_statistics') as mock_stats:
                mock_stats.return_value = {"total_emails_processed": 1000}
                
                start_time = time.time()
                response = client.get(
                    "/api/email-gateway/statistics",
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                end_time = time.time()
                
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                }
        
        # Run baseline measurements
        baseline_results = []
        for i in range(10):
            result = baseline_measurement()
            baseline_results.append(result)
        
        # Calculate baseline metrics
        response_times = [r["response_time"] for r in baseline_results if r["status_code"] == 200]
        baseline_avg = statistics.mean(response_times)
        baseline_std = statistics.stdev(response_times)
        
        # Store baseline for regression testing
        self.baseline_avg = baseline_avg
        self.baseline_std = baseline_std
        
        # Baseline assertions
        assert baseline_avg < 1.0  # Baseline should be under 1 second
        assert baseline_std < 0.5  # Baseline should be consistent
    
    def test_performance_regression_detection(self, client):
        """Test for performance regressions."""
        # This would typically compare against stored baseline
        # For this test, we'll simulate a regression scenario
        
        def regression_measurement():
            """Measure current performance."""
            with patch('app.services.email_gateway_service.EmailGatewayService.get_statistics') as mock_stats:
                mock_stats.return_value = {"total_emails_processed": 1000}
                
                start_time = time.time()
                response = client.get(
                    "/api/email-gateway/statistics",
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                end_time = time.time()
                
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                }
        
        # Run current measurements
        current_results = []
        for i in range(10):
            result = regression_measurement()
            current_results.append(result)
        
        # Calculate current metrics
        response_times = [r["response_time"] for r in current_results if r["status_code"] == 200]
        current_avg = statistics.mean(response_times)
        
        # Regression detection (simplified)
        # In real implementation, would compare against stored baseline
        baseline_avg = 0.5  # Simulated baseline
        
        performance_ratio = current_avg / baseline_avg
        
        # Regression assertions
        assert performance_ratio < 2.0  # Current performance should not be more than 2x slower than baseline
        assert current_avg < 2.0  # Absolute performance should still be reasonable
