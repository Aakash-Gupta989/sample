/**
 * Test All Backend Services
 * Verifies that all backend services are healthy and responding
 */

const testAllBackends = async () => {
  console.log('🧪 Testing All Backend Services...\n');

  const backends = [
    {
      name: 'prepandhire-backend',
      url: 'https://prepandhirebackend.onrender.com'
    },
    {
      name: 'sample',
      url: 'https://sample.onrender.com'
    },
    {
      name: 'sample1',
      url: 'https://sample1.onrender.com'
    }
  ];

  console.log('📋 Backend Health Check Results:');
  console.log('================================');

  let healthyCount = 0;
  let totalCount = backends.length;

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
        console.log(`✅ ${backend.name} is HEALTHY`);
        console.log(`   Status: ${healthData.status}`);
        console.log(`   Instance ID: ${healthData.instance_id}`);
        console.log(`   Timestamp: ${healthData.timestamp}`);
        healthyCount++;
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

  console.log('\n🎯 Backend Test Summary:');
  console.log('========================');
  console.log(`✅ Healthy: ${healthyCount}/${totalCount}`);
  console.log(`❌ Unhealthy: ${totalCount - healthyCount}/${totalCount}`);
  
  if (healthyCount === totalCount) {
    console.log('\n🎉 All backends are healthy! Load balancer is ready.');
  } else if (healthyCount > 0) {
    console.log('\n⚠️ Some backends are healthy. Load balancer will work with available backends.');
  } else {
    console.log('\n❌ No backends are healthy. Check your services.');
  }

  return {
    healthy: healthyCount,
    total: totalCount,
    allHealthy: healthyCount === totalCount
  };
};

// Run the test
testAllBackends().catch(console.error);
