document.addEventListener('DOMContentLoaded', function(){
  const addBtn = document.getElementById('addBtn');
  const addModal = document.getElementById('addModal');
  const closeModal = document.getElementById('closeModal');
  const cancelModal = document.getElementById('cancelModal');
  if(addBtn){
    addBtn.addEventListener('click', ()=>{ addModal.classList.add('open'); addModal.setAttribute('aria-hidden','false'); });
  }
  if(closeModal){ closeModal.addEventListener('click', ()=>{ addModal.classList.remove('open'); addModal.setAttribute('aria-hidden','true'); }); }
  if(cancelModal){ cancelModal.addEventListener('click', ()=>{ addModal.classList.remove('open'); addModal.setAttribute('aria-hidden','true'); }); }

  window.addEventListener('click', function(e){
  if(e.target === addModal){ addModal.classList.remove('open'); addModal.setAttribute('aria-hidden','true'); }
  });

  // Edit modal logic
  const editModal = document.getElementById('editModal');
  const closeEditModal = document.getElementById('closeEditModal');
  const cancelEdit = document.getElementById('cancelEdit');
  const editForm = document.getElementById('editForm');

  // Open edit modal and populate fields when Edit button clicked
  document.querySelectorAll('.edit-btn').forEach(btn => {
    btn.addEventListener('click', function(){
      const row = this.closest('tr');
      const id = row.dataset.id;
      const desc = row.dataset.desc || '';
      const date = row.dataset.date || '';
      const amount = row.dataset.amount || '';
      const category = row.dataset.category || '';

      // populate edit form
      document.getElementById('edit_desc').value = desc;
      document.getElementById('edit_date').value = date;
      document.getElementById('edit_amount').value = amount;
      document.getElementById('edit_category').value = category;

      // set form action to POST to /edit/<id>
      editForm.action = '/edit/' + id;
      editModal.classList.add('open');
      editModal.setAttribute('aria-hidden','false');
    });
  });

  if(closeEditModal){ closeEditModal.addEventListener('click', ()=>{ editModal.classList.remove('open'); editModal.setAttribute('aria-hidden','true'); }); }
  if(cancelEdit){ cancelEdit.addEventListener('click', ()=>{ editModal.classList.remove('open'); editModal.setAttribute('aria-hidden','true'); }); }
  // close edit modal by clicking outside
  window.addEventListener('click', function(e){ if(e.target === editModal){ editModal.classList.remove('open'); editModal.setAttribute('aria-hidden','true'); } });

  // Sidebar logic
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarClose = document.getElementById('sidebarClose');
  if(sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function(e) {
      e.preventDefault();
      sidebar.classList.add('open');
    });
  }
  if(sidebarClose && sidebar) {
    sidebarClose.addEventListener('click', function(e) {
      e.preventDefault();
      sidebar.classList.remove('open');
    });
  }
  // Close sidebar when clicking outside
  window.addEventListener('click', function(e) {
    if(sidebar && sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== sidebarToggle) {
      sidebar.classList.remove('open');
    }
  });
});
