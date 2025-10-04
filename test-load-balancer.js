/**
 * Load Balancer Test Script
 * Tests the load balancer functionality and backend health
 */

const testLoadBalancer = async () => {
  console.log('🧪 Testing Load Balancer Setup...\n');

  const backends = [
    {
      name: 'backend-1',
      url: 'https://prepandhirebackend.onrender.com'
    },
    {
      name: 'backend-2', 
      url: 'https://sample.onrender.com'
    },
    {
      name: 'backend-3',
      url: 'https://sample1.onrender.com'
    }
  ];

  console.log('📋 Testing Backend Health Checks:');
  console.log('================================');

  for (const backend of backends) {
    try {
      console.log(`\n🔍 Testing ${backend.name} (${backend.url})`);
      
      // Test health endpoint
      const healthResponse = await fetch(`${backend.url}/health`, {
        method: 'GET',
        timeout: 10000
      });
      
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        console.log(`✅ ${backend.name} is healthy`);
        console.log(`   Status: ${healthData.status}`);
        console.log(`   Instance ID: ${healthData.instance_id}`);
        console.log(`   Timestamp: ${healthData.timestamp}`);
      } else {
        console.log(`❌ ${backend.name} health check failed: ${healthResponse.status}`);
      }

      // Test main API endpoint
      const apiResponse = await fetch(`${backend.url}/interview/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_description: 'Software Developer',
          resume_text: 'Test resume',
          interview_type: 'technical'
        }),
        timeout: 15000
      });

      if (apiResponse.ok) {
        console.log(`✅ ${backend.name} API is responding`);
      } else {
        console.log(`⚠️ ${backend.name} API returned: ${apiResponse.status}`);
      }

    } catch (error) {
      console.log(`❌ ${backend.name} failed: ${error.message}`);
    }
  }

  console.log('\n🎯 Load Balancer Test Complete!');
  console.log('\n📊 Summary:');
  console.log('- Check which backends are healthy');
  console.log('- Verify API endpoints are working');
  console.log('- Monitor for any connection issues');
};

// Run the test
testLoadBalancer().catch(console.error);
