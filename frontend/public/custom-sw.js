self.addEventListener('push', function(event) {
  let data = {};
  if (event.data) {
    data = event.data.json();
  }
  const title = data.title || 'Invisi-Scan Alert';
  const options = {
    body: data.body || 'New alert from SOC',
    icon: '/pwa-192x192.svg',
    badge: '/favicon.svg'
  };
  event.waitUntil(self.registration.showNotification(title, options));
});
