/**
 * Privik Email Security Chrome Extension
 * Background Service Worker
 */

// Configuration
const CONFIG = {
  serverUrl: 'http://localhost:8000',
  apiKey: '',
  scanInterval: 5000, // 5 seconds
  maxRetries: 3
};

// State management
let state = {
  isEnabled: true,
  threatsDetected: 0,
  lastScan: Date.now(),
  currentTab: null,
  scanQueue: []
};

// Initialize extension
chrome.runtime.onInstalled.addListener((details) => {
  console.log('Privik Email Security extension installed:', details.reason);
  
  // Set default settings
  chrome.storage.local.set({
    isEnabled: true,
    serverUrl: CONFIG.serverUrl,
    apiKey: '',
    notifications: true,
    autoBlock: false
  });
  
  // Create context menu
  chrome.contextMenus.create({
    id: 'privik-scan',
    title: 'Scan with Privik',
    contexts: ['link', 'selection']
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'privik-scan') {
    if (info.linkUrl) {
      scanUrl(info.linkUrl, tab);
    } else if (info.selectionText) {
      scanText(info.selectionText, tab);
    }
  }
});

// Handle tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    // Check if it's an email client
    if (isEmailClient(tab.url)) {
      injectContentScript(tabId);
      startEmailMonitoring(tabId);
    }
  }
});

// Handle tab activation
chrome.tabs.onActivated.addListener((activeInfo) => {
  state.currentTab = activeInfo.tabId;
});

// Handle web requests for link interception
chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    if (details.type === 'main_frame' && isSuspiciousUrl(details.url)) {
      return handleSuspiciousUrl(details);
    }
  },
  { urls: ["<all_urls>"] },
  ["blocking"]
);

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'SCAN_URL':
      scanUrl(message.url, sender.tab).then(sendResponse);
      return true; // Keep message channel open for async response
      
    case 'SCAN_EMAIL':
      scanEmail(message.emailData, sender.tab).then(sendResponse);
      return true;
      
    case 'GET_STATUS':
      sendResponse({
        isEnabled: state.isEnabled,
        threatsDetected: state.threatsDetected,
        lastScan: state.lastScan
      });
      break;
      
    case 'UPDATE_SETTINGS':
      updateSettings(message.settings).then(sendResponse);
      return true;
      
    case 'REPORT_THREAT':
      reportThreat(message.threatData).then(sendResponse);
      return true;
  }
});

/**
 * URL scanning functions
 */

async function scanUrl(url, tab) {
  try {
    console.log('Scanning URL:', url);
    
    // Add to scan queue
    state.scanQueue.push({ url, tab, timestamp: Date.now() });
    
    // Send scan request to server
    const response = await fetch(`${CONFIG.serverUrl}/api/click/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${CONFIG.apiKey}`,
        'X-Extension-Version': '1.0.0'
      },
      body: JSON.stringify({
        url: url,
        user_agent: navigator.userAgent,
        source: 'chrome_extension',
        tab_id: tab?.id
      })
    });
    
    const result = await response.json();
    
    if (result.threat_score > 0) {
      state.threatsDetected++;
      await handleThreat(result, tab);
    }
    
    // Update last scan time
    state.lastScan = Date.now();
    
    // Send result to content script
    if (tab) {
      chrome.tabs.sendMessage(tab.id, {
        type: 'SCAN_RESULT',
        url: url,
        result: result
      });
    }
    
    return result;
    
  } catch (error) {
    console.error('Error scanning URL:', error);
    return { error: error.message };
  }
}

async function scanEmail(emailData, tab) {
  try {
    console.log('Scanning email content');
    
    const response = await fetch(`${CONFIG.serverUrl}/api/ingest/email`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${CONFIG.apiKey}`,
        'X-Extension-Version': '1.0.0'
      },
      body: JSON.stringify({
        ...emailData,
        source: 'chrome_extension',
        tab_id: tab?.id
      })
    });
    
    const result = await response.json();
    
    if (result.threat_score > 0) {
      state.threatsDetected++;
      await handleThreat(result, tab);
    }
    
    return result;
    
  } catch (error) {
    console.error('Error scanning email:', error);
    return { error: error.message };
  }
}

async function scanText(text, tab) {
  try {
    console.log('Scanning text content');
    
    const response = await fetch(`${CONFIG.serverUrl}/api/ai/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${CONFIG.apiKey}`,
        'X-Extension-Version': '1.0.0'
      },
      body: JSON.stringify({
        content: text,
        content_type: 'text',
        source: 'chrome_extension',
        tab_id: tab?.id
      })
    });
    
    const result = await response.json();
    
    if (result.threat_score > 0) {
      state.threatsDetected++;
      await handleThreat(result, tab);
    }
    
    return result;
    
  } catch (error) {
    console.error('Error scanning text:', error);
    return { error: error.message };
  }
}

/**
 * Threat handling functions
 */

async function handleThreat(threatData, tab) {
  try {
    // Show notification
    if (await getSetting('notifications')) {
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon48.png',
        title: 'Privik Security Alert',
        message: `Threat detected: ${threatData.threat_type} (Score: ${threatData.threat_score})`
      });
    }
    
    // Block if auto-block is enabled
    if (await getSetting('autoBlock') && threatData.threat_score > 80) {
      if (tab) {
        chrome.tabs.update(tab.id, { url: 'blocked.html' });
      }
    }
    
    // Send threat data to content script
    if (tab) {
      chrome.tabs.sendMessage(tab.id, {
        type: 'THREAT_DETECTED',
        threat: threatData
      });
    }
    
    // Report to server
    await reportThreat(threatData);
    
  } catch (error) {
    console.error('Error handling threat:', error);
  }
}

async function reportThreat(threatData) {
  try {
    await fetch(`${CONFIG.serverUrl}/api/threat/report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${CONFIG.apiKey}`,
        'X-Extension-Version': '1.0.0'
      },
      body: JSON.stringify({
        ...threatData,
        source: 'chrome_extension',
        timestamp: Date.now()
      })
    });
  } catch (error) {
    console.error('Error reporting threat:', error);
  }
}

/**
 * Email monitoring functions
 */

function startEmailMonitoring(tabId) {
  // Set up periodic scanning for email content
  setInterval(async () => {
    if (state.currentTab === tabId) {
      try {
        await chrome.tabs.sendMessage(tabId, {
          type: 'SCAN_EMAIL_CONTENT'
        });
      } catch (error) {
        // Tab might be closed or content script not ready
      }
    }
  }, CONFIG.scanInterval);
}

/**
 * Utility functions
 */

function isEmailClient(url) {
  const emailDomains = [
    'mail.google.com',
    'outlook.live.com',
    'outlook.office.com',
    'office365.com'
  ];
  
  return emailDomains.some(domain => url.includes(domain));
}

function isSuspiciousUrl(url) {
  const suspiciousPatterns = [
    /bit\.ly/,
    /tinyurl\.com/,
    /goo\.gl/,
    /t\.co/,
    /[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/
  ];
  
  return suspiciousPatterns.some(pattern => pattern.test(url));
}

function handleSuspiciousUrl(details) {
  // Redirect to Privik proxy for analysis
  const proxyUrl = `${CONFIG.serverUrl}/api/click/proxy?url=${encodeURIComponent(details.url)}`;
  
  return {
    redirectUrl: proxyUrl
  };
}

async function injectContentScript(tabId) {
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['injected.js']
    });
  } catch (error) {
    console.error('Error injecting content script:', error);
  }
}

async function updateSettings(newSettings) {
  try {
    await chrome.storage.local.set(newSettings);
    
    // Update local config
    Object.assign(CONFIG, newSettings);
    
    return { success: true };
  } catch (error) {
    console.error('Error updating settings:', error);
    return { error: error.message };
  }
}

async function getSetting(key) {
  try {
    const result = await chrome.storage.local.get(key);
    return result[key];
  } catch (error) {
    console.error('Error getting setting:', error);
    return null;
  }
}

// Periodic cleanup
setInterval(() => {
  // Clean up old scan queue entries
  const now = Date.now();
  state.scanQueue = state.scanQueue.filter(
    entry => now - entry.timestamp < 300000 // 5 minutes
  );
}, 60000); // Every minute
