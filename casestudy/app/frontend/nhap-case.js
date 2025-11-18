document.addEventListener('DOMContentLoaded', () => {
  const API_ENDPOINT = '/api/cases';
  const DRAFT_ENDPOINT = '/api/cases/draft';
  const JSON_SECTION_TYPES = ['skeleton', 'context', 'personas'];
  const JSON_SECTION_LABELS = {
    skeleton: 'Skeleton',
    context: 'Context',
    personas: 'Personas',
  };

  const SECTION_CONFIG = {
    skeleton: {
      basic: [
        {
          key: 'skeleton.case_id',
          label: 'Case ID',
          placeholder: 'ví dụ: case_training_001',
          syncCaseId: true,
        },
        {
          key: 'skeleton.title',
          label: 'Tên case',
          placeholder: 'Tên case hiển thị trong hệ thống',
        },
      ],
      events: [
        { key: 'event.id', label: 'Mã sự kiện', placeholder: 'canon_event_01' },
        { key: 'event.title', label: 'Tiêu đề', placeholder: 'Tên canon event' },
        {
          key: 'event.description',
          label: 'Mô tả chi tiết',
          placeholder: 'Diễn giải tình huống, yếu tố quan trọng...',
          textarea: true,
          rows: 3,
          wide: true,
        },
        {
          key: 'event.npc',
          label: 'NPC xuất hiện',
          placeholder: 'Định dạng: persona_id: vai trò (mỗi dòng hoặc cách nhau bởi dấu phẩy)',
          textarea: true,
          rows: 3,
          wide: true,
        },
        {
          key: 'event.timeout',
          label: 'Timeout (lượt)',
          type: 'number',
          min: 0,
        },
        {
          key: 'event.on_success',
          label: 'On Success',
          placeholder: 'Hệ quả khi hoàn thành canon event',
          textarea: true,
          rows: 3,
          wide: true,
        },
        {
          key: 'event.on_fail',
          label: 'On Fail',
          placeholder: 'Hệ quả khi thất bại',
          textarea: true,
          rows: 3,
          wide: true,
        },
      ],
    },
    context: {
      basic: [
        {
          key: 'context.case_id',
          label: 'Case ID',
          placeholder: 'Sẽ tự động đồng bộ nếu đã có ở tab khác',
          syncCaseId: true,
        },
        {
          key: 'context.topic',
          label: 'Chủ đề case',
          placeholder: 'Ví dụ: Tai nạn giao thông giờ cao điểm',
          wide: true,
        },
      ],
      scene: [
        { key: 'context.scene.time', label: 'Thời gian', placeholder: 'Thời điểm diễn ra' },
        { key: 'context.scene.weather', label: 'Thời tiết', placeholder: 'Nắng, mưa...' },
        {
          key: 'context.scene.location',
          label: 'Vị trí',
          placeholder: 'Địa điểm cụ thể',
          wide: true,
        },
        {
          key: 'context.scene.noise',
          label: 'Mức độ ồn & ghi chú khác',
          placeholder: 'Ghi chú thêm về môi trường',
          textarea: true,
          rows: 3,
          wide: true,
        },
      ],
      indexEvent: [
        {
          key: 'context.index_event.summary',
          label: 'Tóm tắt sự kiện',
          placeholder: 'Mô tả ngắn gọn diễn biến',
          textarea: true,
          rows: 3,
          wide: true,
        },
        {
          key: 'context.index_event.current_state',
          label: 'Tình trạng hiện tại',
          placeholder: 'Điều gì đang diễn ra?',
          textarea: true,
          rows: 3,
          wide: true,
        },
        {
          key: 'context.index_event.who_first',
          label: 'Ai tiếp cận đầu tiên',
          placeholder: 'Nhóm/cá nhân đầu tiên xử lý hiện trường',
          wide: true,
        },
      ],
      notes: [
        {
          key: 'context.constraints',
          label: 'Ràng buộc hiện trường',
          placeholder: 'Mỗi dòng là một ràng buộc',
          textarea: true,
          rows: 3,
          wide: true,
        },
        {
          key: 'context.policies',
          label: 'Chính sách & an toàn',
          placeholder: 'Mỗi dòng là một chính sách cần tuân thủ',
          textarea: true,
          rows: 3,
          wide: true,
        },
        {
          key: 'context.handover',
          label: 'Đơn vị bàn giao',
          placeholder: 'Ví dụ: Bàn giao cho đội cứu trợ địa phương',
          wide: true,
        },
        {
          key: 'context.success_state',
          label: 'Trạng thái thành công cuối cùng',
          placeholder: 'Tình trạng lý tưởng sau khi hoàn thành',
          textarea: true,
          rows: 3,
          wide: true,
        },
      ],
      resources: [
        {
          key: 'context.resource.label',
          label: 'Tên nhóm',
          placeholder: 'Ví dụ: Nhân lực y tế tiền viện',
        },
        {
          key: 'context.resource.note',
          label: 'Ghi chú (tùy chọn)',
          placeholder: 'Ghi chú bổ sung cho nhóm này',
        },
        {
          key: 'context.resource.items',
          label: 'Danh sách nguồn lực',
          placeholder: 'Mỗi dòng là một tài nguyên cụ thể',
          textarea: true,
          rows: 3,
          wide: true,
        },
      ],
    },
    personas: {
      basic: [
        {
          key: 'personas.case_id',
          label: 'Case ID',
          placeholder: 'Sẽ tự động đồng bộ nếu đã có ở tab khác',
          syncCaseId: true,
        },
        {
          key: 'personas.count',
          label: 'Số lượng persona (tham khảo)',
          placeholder: 'Ví dụ: 3',
          type: 'number',
          min: 0,
        },
      ],
      personas: [
        { key: 'persona.id', label: 'Persona ID', placeholder: 'persona_01' },
        { key: 'persona.name', label: 'Tên nhân vật', placeholder: 'Tên hiển thị' },
        { key: 'persona.role', label: 'Vai trò', placeholder: 'Vai trò trong case' },
        { key: 'persona.age', label: 'Tuổi', type: 'number', min: 0 },
        { key: 'persona.gender', label: 'Giới tính', placeholder: 'Nam / Nữ / Khác' },
        {
          key: 'persona.background',
          label: 'Lý lịch / hoàn cảnh',
          placeholder: 'Thông tin nền của nhân vật',
          textarea: true,
          rows: 3,
          wide: true,
        },
        {
          key: 'persona.personality',
          label: 'Tính cách',
          placeholder: 'Đặc điểm tính cách nổi bật',
          textarea: true,
          rows: 3,
          wide: true,
        },
        {
          key: 'persona.goal',
          label: 'Mục tiêu',
          placeholder: 'Điều nhân vật muốn đạt được',
          textarea: true,
          rows: 3,
          wide: true,
        },
        {
          key: 'persona.speech_pattern',
          label: 'Speech pattern',
          placeholder: 'Phong cách giao tiếp',
        },
        {
          key: 'persona.emotion_init',
          label: 'Emotion ban đầu',
          placeholder: 'Cảm xúc khi bắt đầu tình huống',
        },
        {
          key: 'persona.emotion_during',
          label: 'Emotion trong quá trình',
          placeholder: 'Mỗi dòng là một mốc cảm xúc',
          textarea: true,
          rows: 3,
          wide: true,
        },
        {
          key: 'persona.emotion_end',
          label: 'Emotion kết thúc',
          placeholder: 'Cảm xúc khi kết thúc tình huống',
        },
        {
          key: 'persona.voice_tags',
          label: 'Voice tags',
          placeholder: 'Cách nhau bởi dấu phẩy',
          wide: true,
        },
      ],
    },
  };

  const importState = {
    skeleton: null,
    context: null,
    personas: null,
  };

  const tabButtons = Array.from(document.querySelectorAll('[data-tab-target]'));
  const panels = new Map(
    Array.from(document.querySelectorAll('[data-panel]')).map((panel) => [panel.dataset.panel, panel])
  );
  const saveCaseButton = document.querySelector('[data-save-case]');
  const successCriterionTemplate = document.getElementById('success-criterion-template');
  const SUCCESS_LEVEL_SCORES = [5, 4, 3, 2, 1];
  let saveButtonUpdateId = null;

  const controllers = {
    skeleton: createSkeletonController(panels.get('skeleton')),
    context: createContextController(panels.get('context')),
    personas: createPersonasController(panels.get('personas')),
  };

  setupTabs();
  setupNavigation();
  setupJsonImport();
  setupJsonExport();
  setupDraftAgent();
  refreshImportStatuses();
  activateTab('skeleton');
  syncCaseIds();
  scheduleSaveButtonStateUpdate();

  if (saveCaseButton) {
    saveCaseButton.addEventListener('click', handleCaseSave);
  }
  function setupTabs() {
    tabButtons.forEach((button) => {
      button.addEventListener('click', () => {
        const target = button.dataset.tabTarget;
        if (target) {
          activateTab(target);
        }
      });
    });
  }

  function activateTab(tabId) {
    if (!panels.has(tabId)) {
      return;
    }
    tabButtons.forEach((button) => {
      const isActive = button.dataset.tabTarget === tabId;
      button.setAttribute('aria-selected', isActive ? 'true' : 'false');
      button.classList.toggle('bg-primary-600', isActive);
      button.classList.toggle('text-white', isActive);
      button.classList.toggle('shadow', isActive);
      button.classList.toggle('bg-white', !isActive);
      button.classList.toggle('text-primary-600', !isActive);
    });
    panels.forEach((panel, id) => {
      if (id === tabId) {
        panel.classList.remove('hidden');
      } else {
        panel.classList.add('hidden');
      }
    });
  }

  function setupNavigation() {
    document.querySelectorAll('[data-next-tab]').forEach((button) => {
      button.addEventListener('click', () => {
        const target = button.dataset.nextTab;
        if (target) {
          activateTab(target);
        }
      });
    });
    document.querySelectorAll('[data-prev-tab]').forEach((button) => {
      button.addEventListener('click', () => {
        const target = button.dataset.prevTab;
        if (target) {
          activateTab(target);
        }
      });
    });
  }

  function setupJsonImport() {
    JSON_SECTION_TYPES.forEach((type) => {
      const input = document.querySelector(`[data-json-input="${type}"]`);
      const selectBtn = document.querySelector(`[data-json-select="${type}"]`);
      const clearBtn = document.querySelector(`[data-json-clear="${type}"]`);
      const card = document.querySelector(`[data-json-card="${type}"]`);

      if (!input || !card) {
        return;
      }

      card.addEventListener('click', (event) => {
        if (event.target.closest('button')) {
          return;
        }
        input.click();
      });

      if (selectBtn) {
        selectBtn.addEventListener('click', (event) => {
          event.preventDefault();
          input.click();
        });
      }

      if (clearBtn) {
        clearBtn.addEventListener('click', (event) => {
          event.preventDefault();
          clearSectionImport(type);
        });
      }

      input.addEventListener('change', async (event) => {
        const file = event.target.files && event.target.files[0];
        if (!file) {
          return;
        }
        try {
          const content = await readFileAsText(file);
          const parsed = JSON.parse(content);
          applySectionImport(type, parsed, file.name);
        } catch (error) {
          console.error(error);
          showNotification(error.message || 'Không thể đọc file JSON.', 'error');
        } finally {
          input.value = '';
        }
      });
    });
  }

  function setupJsonExport() {
    JSON_SECTION_TYPES.forEach((type) => {
      const button = document.querySelector(`[data-json-export="${type}"]`);
      if (!button) {
        return;
      }
      button.addEventListener('click', (event) => {
        event.preventDefault();
        try {
          const exportEntry = buildSectionExportPayload(type);
          downloadJsonFile(exportEntry.fileName, exportEntry.payload);
          const label = JSON_SECTION_LABELS[type] || type;
          showNotification(`Da luu ${label} ra '${exportEntry.fileName}'.`);
        } catch (error) {
          console.error(error);
          showNotification(error.message || 'Khong the luu file JSON.', 'error');
        }
      });
    });
  }

  function setupDraftAgent() {
    const modal = document.querySelector('[data-draft-modal]');
    if (!modal) {
      return;
    }

    const openButtons = Array.from(document.querySelectorAll('[data-open-draft]'));
    const closeButtons = Array.from(document.querySelectorAll('[data-close-draft]'));
    const form = modal.querySelector('[data-draft-form]');
    const promptInput = modal.querySelector('[data-draft-prompt]');
    const topicInput = modal.querySelector('[data-draft-topic]');
    const personaCountInput = modal.querySelector('[data-draft-persona-count]');
    const locationInput = modal.querySelector('[data-draft-location]');
    const statusLabel = modal.querySelector('[data-draft-status]');
    const submitButton = modal.querySelector('[data-draft-submit]');
    if (!form || !promptInput || !submitButton) {
      return;
    }

    const state = { submitting: false };

    function toggleDraftSubmit(isLoading) {
      state.submitting = isLoading;
      submitButton.disabled = isLoading;
      submitButton.setAttribute('aria-disabled', isLoading ? 'true' : 'false');
      submitButton.classList.toggle('cursor-not-allowed', isLoading);
      submitButton.classList.toggle('opacity-60', isLoading);
    }

    function openModal() {
      modal.classList.remove('hidden');
      modal.classList.add('flex');
      if (statusLabel) {
        statusLabel.textContent = '';
        statusLabel.classList.remove('text-rose-500', 'text-emerald-600');
        statusLabel.classList.add('text-slate-500');
      }
      window.setTimeout(() => {
        promptInput.focus();
      }, 20);
    }

    function closeModal() {
      modal.classList.remove('flex');
      modal.classList.add('hidden');
      form.reset();
      toggleDraftSubmit(false);
      if (statusLabel) {
        statusLabel.textContent = '';
        statusLabel.classList.remove('text-rose-500', 'text-emerald-600');
        statusLabel.classList.add('text-slate-500');
      }
    }

    openButtons.forEach((button) => {
      button.addEventListener('click', () => {
        if (!state.submitting) {
          openModal();
        }
      });
    });

    closeButtons.forEach((button) => {
      button.addEventListener('click', () => {
        if (!state.submitting) {
          closeModal();
        }
      });
    });

    modal.addEventListener('click', (event) => {
      if (event.target === modal && !state.submitting) {
        closeModal();
      }
    });

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (state.submitting) {
        return;
      }

      const payload = buildDraftPayload();
      if (!payload.prompt && !payload.topic) {
        showNotification('Vui lòng nhập prompt hoặc chủ đề trước khi sinh case.', 'error');
        if (statusLabel) {
          statusLabel.textContent = 'Cần nhập prompt hoặc chủ đề.';
          statusLabel.classList.remove('text-slate-500', 'text-emerald-600');
          statusLabel.classList.add('text-rose-500');
        }
        return;
      }

      try {
        toggleDraftSubmit(true);
        if (statusLabel) {
          statusLabel.textContent = 'Đang sinh case từ agent...';
          statusLabel.classList.remove('text-rose-500', 'text-emerald-600');
          statusLabel.classList.add('text-slate-500');
        }
        const response = await fetch(DRAFT_ENDPOINT, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || 'Agent gợi ý trả về lỗi.');
        }
        const draft = await response.json();
        applyDraftToForms(draft);
        closeModal();
        showNotification(`Đã sinh case gợi ý '${draft.case_id}'.`);
        if (Array.isArray(draft.warnings)) {
          draft.warnings.forEach((message) => {
            if (message) {
              showNotification(message, 'info');
            }
          });
        }
      } catch (error) {
        console.error(error);
        const message = error?.message || 'Không thể sinh case tự động.';
        showNotification(message, 'error');
        if (statusLabel) {
          statusLabel.textContent = message;
          statusLabel.classList.remove('text-slate-500', 'text-emerald-600');
          statusLabel.classList.add('text-rose-500');
        }
      } finally {
        toggleDraftSubmit(false);
      }
    });

    function buildDraftPayload() {
      const prompt = promptInput.value.trim();
      const topic = topicInput ? topicInput.value.trim() : '';
      const location = locationInput ? locationInput.value.trim() : '';
      const personaCountRaw = personaCountInput ? personaCountInput.value.trim() : '';
      const personaCount = personaCountRaw ? Number.parseInt(personaCountRaw, 10) : NaN;

      const payload = {
        prompt,
        ensure_minimum_personas: true,
      };
      if (topic) {
        payload.topic = topic;
      }
      if (location) {
        payload.location = location;
      }
      if (Number.isFinite(personaCount) && personaCount > 0) {
        payload.persona_count = personaCount;
      }
      return payload;
    }
  }

  function applyDraftToForms(draft) {
    if (!draft) {
      return;
    }
    const caseId = draft.case_id || '';
    const skeleton = draft.skeleton || {};
    const context = draft.context || {};
    const personasPayload = draft.personas || {};
    const personaList = Array.isArray(personasPayload.personas) ? personasPayload.personas : [];
    const personaData = {
      case_id: personasPayload.case_id || caseId,
      personas: personaList,
      count: personaList.length,
    };

    controllers.skeleton.write(skeleton);
    controllers.context.write(context);
    controllers.personas.write(personaData);

    importState.skeleton = { data: skeleton, fileName: 'draft-agent', caseId };
    importState.context = { data: context, fileName: 'draft-agent', caseId };
    importState.personas = { data: personaData, fileName: 'draft-agent', caseId };

    syncCaseIds(caseId);
    updateImportStatus('skeleton');
    updateImportStatus('context');
    updateImportStatus('personas');
    activateTab('skeleton');
    scheduleSaveButtonStateUpdate();
  }
  function applySectionImport(type, parsed, fileName) {
    try {
      const normalized = normalizeSectionPayload(type, parsed);
      const caseId = normalized.caseId || getAggregatedCaseId();

      importState[type] = {
        data: normalized.data,
        fileName,
        caseId: caseId || '',
      };

      if (type === 'skeleton') {
        controllers.skeleton.write(normalized.data);
      } else if (type === 'context') {
        controllers.context.write(normalized.data);
      } else if (type === 'personas') {
        controllers.personas.write(normalized.data);
      }

      if (caseId) {
        controllers.skeleton.setCaseId(caseId, { force: true });
        controllers.context.setCaseId(caseId, { force: true });
        controllers.personas.setCaseId(caseId, { force: true });
      } else {
        syncCaseIds();
      }

      updateImportStatus(type);
      showNotification(`Đã nạp ${JSON_SECTION_LABELS[type]} từ '${fileName}'.`);
      activateTab(type);
      scheduleSaveButtonStateUpdate();
    } catch (error) {
      console.error(error);
      showNotification(error.message || 'Không thể nạp dữ liệu từ file JSON.', 'error');
    }
  }

  function clearSectionImport(type, options = {}) {
    if (importState[type]) {
      importState[type] = null;
    }

    if (type === 'skeleton') {
      controllers.skeleton.reset();
    } else if (type === 'context') {
      controllers.context.reset();
    } else if (type === 'personas') {
      controllers.personas.reset();
    }

    updateImportStatus(type);
    syncCaseIds();
    scheduleSaveButtonStateUpdate();

    if (!options.silent) {
      showNotification(`Đã xóa dữ liệu ${JSON_SECTION_LABELS[type]} khỏi biểu mẫu.`, 'info');
    }
  }

  function refreshImportStatuses() {
    JSON_SECTION_TYPES.forEach(updateImportStatus);
  }

  function updateImportStatus(type) {
    const statusEl = document.querySelector(`[data-json-status="${type}"]`);
    if (!statusEl) {
      return;
    }
    const entry = importState[type];
    if (!entry) {
      statusEl.textContent = 'Chưa chọn file';
      return;
    }

    const summaryParts = [entry.fileName];
    if (entry.caseId) {
      summaryParts.push(`case ${entry.caseId}`);
    }
    if (type === 'skeleton') {
      const count = Array.isArray(entry.data?.canon_events) ? entry.data.canon_events.length : 0;
      if (count) {
        summaryParts.push(`${count} canon event`);
      }
    } else if (type === 'context') {
      const available = entry.data?.initial_context?.available_resources;
      const count = available && typeof available === 'object' ? Object.keys(available).length : 0;
      if (count) {
        summaryParts.push(`${count} nhóm resource`);
      }
    } else if (type === 'personas') {
      const count = Array.isArray(entry.data?.personas) ? entry.data.personas.length : 0;
      if (count) {
        summaryParts.push(`${count} personas`);
      }
    }

    statusEl.textContent = summaryParts.join(' • ');
  }

  function buildSectionExportPayload(type) {
    if (type === 'skeleton') {
      const skeleton = controllers.skeleton.read() || {};
      const caseId = skeleton.case_id || getAggregatedCaseId() || `draft_${type}`;
      const normalizedSkeleton = { ...skeleton, case_id: skeleton.case_id || caseId };
      const slug = slugify(caseId, `case-${type}`);
      return {
        fileName: `${slug}-skeleton.json`,
        payload: {
          case_id: caseId,
          skeleton: normalizedSkeleton,
        },
      };
    }

    if (type === 'context') {
      const context = controllers.context.read() || {};
      const caseId = context.case_id || getAggregatedCaseId() || `draft_${type}`;
      const normalizedContext = { ...context, case_id: context.case_id || caseId };
      const slug = slugify(caseId, `case-${type}`);
      return {
        fileName: `${slug}-context.json`,
        payload: {
          case_id: caseId,
          context: normalizedContext,
        },
      };
    }

    if (type === 'personas') {
      const personasPayload = controllers.personas.read() || {};
      const caseId = personasPayload.case_id || getAggregatedCaseId() || `draft_${type}`;
      const normalizedPersonas = { ...personasPayload, case_id: personasPayload.case_id || caseId };
      const slug = slugify(caseId, `case-${type}`);
      return {
        fileName: `${slug}-personas.json`,
        payload: {
          case_id: caseId,
          personas: normalizedPersonas,
        },
      };
    }

    throw new Error('Loai file khong duoc ho tro.');
  }

  function downloadJsonFile(fileName, payload) {
    const json = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => {
      URL.revokeObjectURL(url);
    }, 0);
  }

  function handleCaseSave(event) {
    event.preventDefault();
    const validation = getValidationState();

    if (!validation.isComplete) {
      const message = formatMissingMessages(validation.issues);
      showNotification(
        message
          ? `Vui lòng bổ sung thông tin trước khi lưu: ${message}`
          : 'Vui lòng hoàn thiện cả 3 biểu mẫu trước khi lưu.',
        'error'
      );

      if (validation.issues.skeleton.length) {
        activateTab('skeleton');
      } else if (validation.issues.context.length) {
        activateTab('context');
      } else {
        activateTab('personas');
      }
      return;
    }

    const payload = buildCasePayload();
    submitCasePayload(payload);
  }

  async function submitCasePayload(payload) {
    if (!saveCaseButton) {
      return;
    }

    toggleButtonState(saveCaseButton, true);

    try {
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || 'Máy chủ trả về lỗi.');
      }

      const responseData = await response.json().catch(() => null);
      const resolvedCaseId = responseData?.case_id ?? payload.case_id;
      const personasCount =
        responseData?.personas_count ??
        payload.personas?.personas?.length ??
        (Array.isArray(payload.personas) ? payload.personas.length : 0);
      const serverMessage = responseData?.message?.trim();
      const fallbackMessage = `Đã lưu case '${resolvedCaseId}' thành công${
        personasCount ? ` (${personasCount} personas)` : ''
      }.`;
      const message = serverMessage || fallbackMessage;
      const notificationType =
        serverMessage && serverMessage.toLowerCase().includes('không thể kết nối mongodb')
          ? 'info'
          : 'success';
      showNotification(message, notificationType);
    } catch (error) {
      console.error(error);
      showNotification(error.message || 'Không thể lưu case.', 'error');
    } finally {
      toggleButtonState(saveCaseButton, false);
    }
  }
  function createSkeletonController(panel) {
    if (!panel) {
      throw new Error('Không tìm thấy panel Skeleton.');
    }
    const form = panel.querySelector('[data-form="skeleton"]');
    const basicHost = form.querySelector('[data-basic-fields]');
    const eventsHost = form.querySelector('[data-list="canon-events"]');
    const addButton = form.querySelector('[data-add-event]');

    SECTION_CONFIG.skeleton.basic.forEach((field) => {
      const fieldEl = createField(field);
      if (field.wide) {
        fieldEl.wrapper.classList.add('md:col-span-2');
      }
      basicHost.appendChild(fieldEl.wrapper);
    });

    function createEventBlock() {
      const block = document.createElement('article');
      block.className = 'space-y-4 rounded-2xl border border-slate-200 bg-white/80 p-5 shadow-sm';
      block.dataset.block = 'event';

      const header = document.createElement('div');
      const title = document.createElement('h4');
      title.className = 'text-sm font-semibold text-slate-900';
      title.dataset.blockTitle = 'Canon Event';
      header.appendChild(title);
      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'text-xs font-semibold text-rose-600 transition hover:text-rose-500';
      removeBtn.textContent = 'Xóa';
      header.appendChild(removeBtn);
      block.appendChild(header);

      const grid = document.createElement('div');
      grid.className = 'grid gap-4 md:grid-cols-2';
      SECTION_CONFIG.skeleton.events.forEach((field) => {
        const fieldEl = createField(field);
        if (field.wide) {
          fieldEl.wrapper.classList.add('md:col-span-2');
        }
        grid.appendChild(fieldEl.wrapper);
      });
      block.appendChild(grid);

      block.appendChild(buildSuccessCriteriaSection());
      setupSuccessCriteriaSection(block);

      removeBtn.addEventListener('click', () => {
        if (eventsHost.children.length === 1) {
          resetFields(block);
        } else {
          block.remove();
          renumberBlocks(eventsHost, 'Canon Event');
        }
        scheduleSaveButtonStateUpdate();
      });

      return block;
    }

    function ensureEventBlock() {
      if (!eventsHost.children.length) {
        eventsHost.appendChild(createEventBlock());
      }
      renumberBlocks(eventsHost, 'Canon Event');
    }

    ensureEventBlock();

    if (addButton) {
      addButton.addEventListener('click', () => {
        eventsHost.appendChild(createEventBlock());
        renumberBlocks(eventsHost, 'Canon Event');
        scheduleSaveButtonStateUpdate();
      });
    }

    return {
      read() {
        const caseId = getFieldValue(form, 'skeleton.case_id');
        const title = getFieldValue(form, 'skeleton.title');
        const events = Array.from(eventsHost.children)
          .map((block, index) => readEventBlock(block, index))
          .filter(Boolean);
        return {
          case_id: caseId,
          title,
          canon_events: events,
        };
      },
      write(data = {}) {
        setFieldValue(form, 'skeleton.case_id', data.case_id || '');
        setFieldValue(form, 'skeleton.title', data.title || '');
        eventsHost.innerHTML = '';
        const events = Array.isArray(data.canon_events) && data.canon_events.length ? data.canon_events : [{}];
        events.forEach((event) => {
          const block = createEventBlock();
          eventsHost.appendChild(block);
          fillEventBlock(block, event);
        });
        renumberBlocks(eventsHost, 'Canon Event');
      },
      reset() {
        setFieldValue(form, 'skeleton.case_id', '');
        setFieldValue(form, 'skeleton.title', '');
        eventsHost.innerHTML = '';
        ensureEventBlock();
      },
      getCaseId() {
        return getFieldValue(form, 'skeleton.case_id');
      },
      setCaseId(value, options = {}) {
        const field = form.querySelector('[data-field="skeleton.case_id"]');
        applyCaseId(field, value, options);
      },
    };
  }

  function createContextController(panel) {
    if (!panel) {
      throw new Error('Không tìm thấy panel Context.');
    }
    const form = panel.querySelector('[data-form="context"]');
    const basicHost = form.querySelector('[data-basic-fields]');
    const sceneHost = form.querySelector('[data-scene-fields]');
    const indexEventHost = form.querySelector('[data-index-event-fields]');
    const notesHost = form.querySelector('[data-context-notes]');
    const resourcesHost = form.querySelector('[data-list="resources"]');
    const addButton = form.querySelector('[data-add-resource]');

    SECTION_CONFIG.context.basic.forEach((field) => {
      const fieldEl = createField(field);
      if (field.wide) {
        fieldEl.wrapper.classList.add('md:col-span-2');
      }
      basicHost.appendChild(fieldEl.wrapper);
    });

    SECTION_CONFIG.context.scene.forEach((field) => {
      const fieldEl = createField(field);
      if (field.wide) {
        fieldEl.wrapper.classList.add('md:col-span-2');
      }
      sceneHost.appendChild(fieldEl.wrapper);
    });

    SECTION_CONFIG.context.indexEvent.forEach((field) => {
      const fieldEl = createField(field);
      if (field.wide) {
        fieldEl.wrapper.classList.add('md:col-span-2');
      }
      indexEventHost.appendChild(fieldEl.wrapper);
    });

    SECTION_CONFIG.context.notes.forEach((field) => {
      const fieldEl = createField(field);
      if (field.wide) {
        fieldEl.wrapper.classList.add('md:col-span-2');
      }
      notesHost.appendChild(fieldEl.wrapper);
    });

    function createResourceBlock() {
      const block = document.createElement('article');
      block.className = 'space-y-4 rounded-2xl border border-slate-200 bg-white/80 p-5 shadow-sm';
      block.dataset.block = 'resource';

      const header = document.createElement('div');
      header.className = 'flex items-center justify-between';
      const title = document.createElement('h4');
      title.className = 'text-sm font-semibold text-slate-900';
      title.dataset.blockTitle = 'Resource';
      header.appendChild(title);
      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'text-xs font-semibold text-rose-600 transition hover:text-rose-500';
      removeBtn.textContent = 'Xóa';
      header.appendChild(removeBtn);
      block.appendChild(header);

      const grid = document.createElement('div');
      grid.className = 'grid gap-4 md:grid-cols-2';
      SECTION_CONFIG.context.resources.forEach((field) => {
        const fieldEl = createField(field);
        if (field.wide) {
          fieldEl.wrapper.classList.add('md:col-span-2');
        }
        grid.appendChild(fieldEl.wrapper);
      });
      block.appendChild(grid);

      removeBtn.addEventListener('click', () => {
        if (resourcesHost.children.length === 1) {
          resetFields(block);
        } else {
          block.remove();
          renumberBlocks(resourcesHost, 'Resource');
        }
        scheduleSaveButtonStateUpdate();
      });

      return block;
    }

    function ensureResourceBlock() {
      if (!resourcesHost.children.length) {
        resourcesHost.appendChild(createResourceBlock());
      }
      renumberBlocks(resourcesHost, 'Resource');
    }

    ensureResourceBlock();

    if (addButton) {
      addButton.addEventListener('click', () => {
        resourcesHost.appendChild(createResourceBlock());
        renumberBlocks(resourcesHost, 'Resource');
        scheduleSaveButtonStateUpdate();
      });
    }

    return {
      read() {
        const caseId = getFieldValue(form, 'context.case_id');
        const topic = getFieldValue(form, 'context.topic');

        const scene = {
          time: getFieldValue(form, 'context.scene.time'),
          weather: getFieldValue(form, 'context.scene.weather'),
          location: getFieldValue(form, 'context.scene.location'),
          noise_level: getFieldValue(form, 'context.scene.noise'),
        };

        const indexEvent = {
          summary: getFieldValue(form, 'context.index_event.summary'),
          current_state: getFieldValue(form, 'context.index_event.current_state'),
          who_first_on_scene: getFieldValue(form, 'context.index_event.who_first'),
        };

        const resourceBlocks = Array.from(resourcesHost.children);
        const availableResources = {};
        const availableResourcesMeta = {};
        const used = new Set();

        resourceBlocks.forEach((block, index) => {
          const label = getFieldValue(block, 'context.resource.label');
          const note = getFieldValue(block, 'context.resource.note');
          const items = splitLines(getFieldValue(block, 'context.resource.items'));
          if (!label && !note && !items.length) {
            return;
          }
          const base = slugify(label, `resource_${index + 1}`);
          let key = base;
          let counter = 2;
          while (used.has(key)) {
            key = `${base}_${counter}`;
            counter += 1;
          }
          used.add(key);

          const payloadItems = items.slice();
          if (note) {
            payloadItems.push(`NOTE: ${note}`);
          }

          availableResources[key] = payloadItems;
          availableResourcesMeta[key] = {
            label: label || `Nhóm ${index + 1}`,
            note: note || '',
          };
        });

        const constraints = splitLines(getFieldValue(form, 'context.constraints'));
        const policies = splitLines(getFieldValue(form, 'context.policies'));
        const handover = getFieldValue(form, 'context.handover');
        const successState = getFieldValue(form, 'context.success_state');

        const initialContext = {
          scene,
          index_event: indexEvent,
          available_resources: availableResources,
          constraints,
          policies_safety_legal: policies,
          handover_target: handover,
          success_end_state: successState,
        };

        if (Object.keys(availableResourcesMeta).length) {
          initialContext.available_resources_meta = availableResourcesMeta;
        }

        return {
          case_id: caseId,
          topic,
          initial_context: initialContext,
        };
      },
      write(data = {}) {
        const initial = data.initial_context || {};
        const scene = initial.scene || data.scene || {};
        const indexEvent = initial.index_event || data.index_event || {};

        setFieldValue(form, 'context.case_id', data.case_id || '');
        setFieldValue(form, 'context.topic', data.topic || '');
        setFieldValue(form, 'context.scene.time', scene.time || '');
        setFieldValue(form, 'context.scene.weather', scene.weather || '');
        setFieldValue(form, 'context.scene.location', scene.location || '');
        setFieldValue(form, 'context.scene.noise', scene.noise_level || scene.noise || '');
        setFieldValue(form, 'context.index_event.summary', indexEvent.summary || '');
        setFieldValue(form, 'context.index_event.current_state', indexEvent.current_state || '');
        setFieldValue(
          form,
          'context.index_event.who_first',
          indexEvent.who_first_on_scene || indexEvent.who_first || ''
        );
        setFieldValue(form, 'context.constraints', joinLines(initial.constraints || data.constraints));
        setFieldValue(
          form,
          'context.policies',
          joinLines(initial.policies_safety_legal || initial.policies || data.policies)
        );
        setFieldValue(
          form,
          'context.handover',
          initial.handover_target || data.handover_target || data.handover || ''
        );
        setFieldValue(
          form,
          'context.success_state',
          initial.success_end_state || data.success_end_state || ''
        );

        resourcesHost.innerHTML = '';
        const unpackedResources = unpackResources(initial);
        const targetResources = unpackedResources.length ? unpackedResources : [{}];
        targetResources.forEach((resource) => {
          const block = createResourceBlock();
          resourcesHost.appendChild(block);
          setFieldValue(block, 'context.resource.label', resource.label || '');
          setFieldValue(block, 'context.resource.note', resource.note || '');
          setFieldValue(block, 'context.resource.items', joinLines(resource.items));
        });
        renumberBlocks(resourcesHost, 'Resource');
      },
      reset() {
        setFieldValue(form, 'context.case_id', '');
        setFieldValue(form, 'context.topic', '');
        sceneHost.querySelectorAll('[data-field]').forEach((field) => (field.value = ''));
        indexEventHost.querySelectorAll('[data-field]').forEach((field) => (field.value = ''));
        notesHost.querySelectorAll('[data-field]').forEach((field) => (field.value = ''));
        resourcesHost.innerHTML = '';
        ensureResourceBlock();
      },
      getCaseId() {
        return getFieldValue(form, 'context.case_id');
      },
      setCaseId(value, options = {}) {
        const field = form.querySelector('[data-field="context.case_id"]');
        applyCaseId(field, value, options);
      },
    };
  }
  function createPersonasController(panel) {
    if (!panel) {
      throw new Error('Không tìm thấy panel Personas.');
    }
    const form = panel.querySelector('[data-form="personas"]');
    const basicHost = form.querySelector('[data-basic-fields]');
    const listHost = form.querySelector('[data-list="personas"]');
    const addButton = form.querySelector('[data-add-persona]');

    SECTION_CONFIG.personas.basic.forEach((field) => {
      const fieldEl = createField(field);
      if (field.wide) {
        fieldEl.wrapper.classList.add('md:col-span-2');
      }
      basicHost.appendChild(fieldEl.wrapper);
    });

    function createPersonaBlock() {
      const block = document.createElement('article');
      block.className = 'space-y-4 rounded-2xl border border-slate-200 bg-white/80 p-5 shadow-sm';
      block.dataset.block = 'persona';

      const header = document.createElement('div');
      header.className = 'flex items-center justify-between';
      const title = document.createElement('h4');
      title.className = 'text-sm font-semibold text-slate-900';
      title.dataset.blockTitle = 'Persona';
      header.appendChild(title);
      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'text-xs font-semibold text-rose-600 transition hover:text-rose-500';
      removeBtn.textContent = 'Xóa';
      header.appendChild(removeBtn);
      block.appendChild(header);

      const grid = document.createElement('div');
      grid.className = 'grid gap-4 md:grid-cols-2';
      SECTION_CONFIG.personas.personas.forEach((field) => {
        const fieldEl = createField(field);
        if (field.wide) {
          fieldEl.wrapper.classList.add('md:col-span-2');
        }
        grid.appendChild(fieldEl.wrapper);
      });
      block.appendChild(grid);

      removeBtn.addEventListener('click', () => {
        if (listHost.children.length === 1) {
          resetFields(block);
        } else {
          block.remove();
          renumberBlocks(listHost, 'Persona');
        }
        scheduleSaveButtonStateUpdate();
      });

      return block;
    }

    function ensurePersonaBlock() {
      if (!listHost.children.length) {
        listHost.appendChild(createPersonaBlock());
      }
      renumberBlocks(listHost, 'Persona');
    }

    ensurePersonaBlock();

    if (addButton) {
      addButton.addEventListener('click', () => {
        listHost.appendChild(createPersonaBlock());
        renumberBlocks(listHost, 'Persona');
        scheduleSaveButtonStateUpdate();
      });
    }

    return {
      read() {
        const caseId = getFieldValue(form, 'personas.case_id');
        const countRaw = getFieldValue(form, 'personas.count');
        const count = countRaw ? Number.parseInt(countRaw, 10) : null;
        const personas = Array.from(listHost.children)
          .map((block, index) => readPersonaBlock(block, index))
          .filter(Boolean);
        return {
          case_id: caseId,
          count: Number.isFinite(count) ? count : null,
          personas,
        };
      },
      write(data = {}) {
        setFieldValue(form, 'personas.case_id', data.case_id || '');
        setFieldValue(form, 'personas.count', data.count != null ? String(data.count) : '');
        listHost.innerHTML = '';
        const personas = Array.isArray(data.personas) && data.personas.length ? data.personas : [{}];
        personas.forEach((persona) => {
          const block = createPersonaBlock();
          listHost.appendChild(block);
          fillPersonaBlock(block, persona);
        });
        renumberBlocks(listHost, 'Persona');
      },
      reset() {
        setFieldValue(form, 'personas.case_id', '');
        setFieldValue(form, 'personas.count', '');
        listHost.innerHTML = '';
        ensurePersonaBlock();
      },
      getCaseId() {
        return getFieldValue(form, 'personas.case_id');
      },
      setCaseId(value, options = {}) {
        const field = form.querySelector('[data-field="personas.case_id"]');
        applyCaseId(field, value, options);
      },
    };
  }

  function unpackResources(initial) {
    const available = initial.available_resources;
    if (!available || typeof available !== 'object') {
      return [];
    }
    const meta = initial.available_resources_meta || {};
    return Object.keys(available).map((key, index) => {
      const items = Array.isArray(available[key]) ? available[key] : [];
      let note = '';
      const cleanedItems = [];
      items.forEach((raw) => {
        const value = String(raw || '').trim();
        if (!value) {
          return;
        }
        if (!note && value.toUpperCase().startsWith('NOTE:')) {
          note = value.replace(/^NOTE:\s*/i, '');
        } else {
          cleanedItems.push(value);
        }
      });
      const metaEntry = meta[key] || {};
      return {
        key,
        label: metaEntry.label || key || `Resource ${index + 1}`,
        note: metaEntry.note || note,
        items: cleanedItems,
      };
    });
  }

  function createField(fieldConfig) {
    const wrapper = document.createElement('label');
    wrapper.className = 'flex flex-col gap-2 text-left';
    const label = document.createElement('span');
    label.className = 'text-xs font-semibold uppercase tracking-wide text-slate-500';
    label.textContent = fieldConfig.label;
    wrapper.appendChild(label);

    const control = fieldConfig.textarea ? document.createElement('textarea') : document.createElement('input');
    control.className = 'w-full rounded-xl border border-slate-200 bg-white/80 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-200';
    control.dataset.field = fieldConfig.key;
    control.placeholder = fieldConfig.placeholder || '';
    control.autocomplete = 'off';

    if (fieldConfig.textarea) {
      control.rows = fieldConfig.rows || 3;
    } else {
      control.type = fieldConfig.type || 'text';
      if (fieldConfig.type === 'number' && fieldConfig.min != null) {
        control.min = String(fieldConfig.min);
      }
    }

    control.addEventListener('input', () => scheduleSaveButtonStateUpdate());
    if (fieldConfig.syncCaseId) {
      control.addEventListener('blur', () => syncCaseIds(control.value.trim() || undefined));
    }

    wrapper.appendChild(control);
    return { wrapper, control };
  }

  function applyCaseId(field, value, options = {}) {
    if (!field) {
      return;
    }
    const { force = false } = options;
    const nextValue = value != null ? String(value) : '';
    if (!force && !nextValue) {
      return;
    }
    if (!force && field.value && field.value.trim()) {
      return;
    }
    field.value = nextValue;
  }

  function getFieldValue(root, key) {
    const field = root ? root.querySelector(`[data-field="${key}"]`) : null;
    return field ? field.value.trim() : '';
  }

  function setFieldValue(root, key, value) {
    const field = root ? root.querySelector(`[data-field="${key}"]`) : null;
    if (!field) {
      return;
    }
    field.value = value == null ? '' : String(value);
  }

  function resetFields(root) {
    if (!root) {
      return;
    }
    root.querySelectorAll('input, textarea').forEach((field) => {
      field.value = '';
    });
    resetSuccessCriteria(root);
  }

  function buildSuccessCriteriaSection() {
    const wrapper = document.createElement('div');
    wrapper.className = 'mt-4 space-y-3';

    const header = document.createElement('div');
    header.className = 'flex flex-wrap items-center justify-between gap-3';
    const label = document.createElement('span');
    label.className = 'text-xs font-semibold uppercase tracking-wide text-slate-500';
    label.textContent = 'Success Criteria';
    header.appendChild(label);

    const addBtn = document.createElement('button');
    addBtn.type = 'button';
    addBtn.className =
      'text-xs font-semibold text-primary-600 transition hover:text-primary-500 focus:outline-none';
    addBtn.textContent = 'Thêm tiêu chí';
    addBtn.setAttribute('data-add-success-criterion', '');
    header.appendChild(addBtn);
    wrapper.appendChild(header);

    const helper = document.createElement('p');
    helper.className = 'text-xs text-slate-500';
    helper.textContent = 'Mỗi tiêu chí gồm phần mô tả và 5 mức đánh giá (điểm 5 đến 1).';
    wrapper.appendChild(helper);

    const list = document.createElement('div');
    list.className = 'space-y-4';
    list.setAttribute('data-success-criteria-list', '');
    wrapper.appendChild(list);

    return wrapper;
  }

  function initSuccessCriterionItem(item, list) {
    if (!item || !list) {
      return;
    }
    const removeBtn = item.querySelector('[data-remove-success-criterion]');
    if (removeBtn && !removeBtn.dataset.bound) {
      removeBtn.dataset.bound = 'true';
      removeBtn.addEventListener('click', () => {
        if (list.children.length === 1) {
          item.querySelectorAll('input, textarea').forEach((field) => {
            field.value = '';
          });
        } else {
          item.remove();
        }
        scheduleSaveButtonStateUpdate();
      });
    }

    item.querySelectorAll('input, textarea').forEach((field) => {
      if (!field.dataset.successCriteriaWatcher) {
        field.dataset.successCriteriaWatcher = 'true';
        field.addEventListener('input', () => scheduleSaveButtonStateUpdate());
      }
    });
  }

  function appendSuccessCriterionItem(list, options = {}) {
    if (!list || !successCriterionTemplate) {
      return null;
    }
    const clone = successCriterionTemplate.content.firstElementChild.cloneNode(true);
    list.appendChild(clone);
    initSuccessCriterionItem(clone, list);
    if (!options.silent) {
      scheduleSaveButtonStateUpdate();
    }
    return clone;
  }

  function setupSuccessCriteriaSection(block) {
    const list = block.querySelector('[data-success-criteria-list]');
    const addBtn = block.querySelector('[data-add-success-criterion]');
    if (!list) {
      return;
    }

    if (!list.children.length) {
      appendSuccessCriterionItem(list, { silent: true });
    } else {
      list.querySelectorAll('[data-success-criterion]').forEach((item) =>
        initSuccessCriterionItem(item, list)
      );
    }

    if (addBtn && !addBtn.dataset.successCriteriaInit) {
      addBtn.dataset.successCriteriaInit = 'true';
      addBtn.addEventListener('click', () => {
        appendSuccessCriterionItem(list);
      });
    }
  }

  function resetSuccessCriteria(root) {
    const list = root.querySelector('[data-success-criteria-list]');
    if (!list) {
      return;
    }
    const items = Array.from(list.querySelectorAll('[data-success-criterion]'));
    items.forEach((item, index) => {
      if (index === 0) {
        item.querySelectorAll('input, textarea').forEach((field) => {
          field.value = '';
        });
      } else {
        item.remove();
      }
    });
  }

  function normalizeSuccessCriteriaInput(raw) {
    if (!Array.isArray(raw)) {
      if (typeof raw === 'string' && raw.trim()) {
        return [
          {
            description: raw.trim(),
            levels: SUCCESS_LEVEL_SCORES.map((score) => ({ score, descriptor: '' })),
          },
        ];
      }
      return [];
    }

    return raw
      .map((item, index) => {
        if (item && typeof item === 'object') {
          const description = String(item.description || '').trim();
          const levelMap = {};
          (Array.isArray(item.levels) ? item.levels : []).forEach((level) => {
            const score = Number(level?.score);
            const descriptor = typeof level?.descriptor === 'string' ? level.descriptor.trim() : '';
            if (descriptor && SUCCESS_LEVEL_SCORES.includes(score)) {
              levelMap[score] = descriptor;
            }
          });
          const normalizedLevels = SUCCESS_LEVEL_SCORES.map((score) => ({
            score,
            descriptor: levelMap[score] || '',
          }));
          if (!description && !normalizedLevels.some((level) => level.descriptor)) {
            return null;
          }
          return { description, levels: normalizedLevels };
        }
        const description = String(item || '').trim();
        if (!description) {
          return null;
        }
        return {
          description,
          levels: SUCCESS_LEVEL_SCORES.map((score) => ({ score, descriptor: '' })),
        };
      })
      .filter(Boolean);
  }

  function fillSuccessCriteria(block, rawData) {
    const list = block.querySelector('[data-success-criteria-list]');
    if (!list) {
      return;
    }
    list.innerHTML = '';
    const criteria = normalizeSuccessCriteriaInput(rawData);
    const targets = criteria.length ? criteria : [{}];
    targets.forEach((criterion) => {
      const item = appendSuccessCriterionItem(list, { silent: true });
      if (!item) {
        return;
      }
      const descriptionField = item.querySelector('[data-criterion-description]');
      if (descriptionField) {
        descriptionField.value = criterion.description || '';
      }
      SUCCESS_LEVEL_SCORES.forEach((score) => {
        const field = item.querySelector(`[data-level-descriptor="${score}"]`);
        if (field) {
          const descriptor =
            (criterion.levels || []).find((level) => Number(level.score) === score)?.descriptor || '';
          field.value = descriptor || '';
        }
      });
    });
  }

  function collectSuccessCriteria(eventBlock) {
    if (!eventBlock) return [];
    const list = eventBlock.querySelector('[data-success-criteria-list]');
    if (!list) return [];

    return Array.from(list.querySelectorAll('[data-success-criterion]'))
      .map((criterion) => {
        const description = (
          criterion.querySelector('[data-criterion-description]')?.value || ''
        ).trim();
        const levels = SUCCESS_LEVEL_SCORES.map((score) => {
          const descriptor = (
            criterion.querySelector(`[data-level-descriptor="${score}"]`)?.value || ''
          ).trim();
          return { score, descriptor };
        });
        const hasLevelDetails = levels.some((level) => level.descriptor);
        if (!description && !hasLevelDetails) {
          return null;
        }
        return {
          description,
          levels,
        };
      })
      .filter(Boolean);
  }
  function readEventBlock(block, index) {
    const id = getFieldValue(block, 'event.id');
    const title = getFieldValue(block, 'event.title');
    const description = getFieldValue(block, 'event.description');
    const successCriteria = collectSuccessCriteria(block);
    const npcText = getFieldValue(block, 'event.npc');
    const npcAppearance = parseNpcText(npcText);
    const timeoutRaw = getFieldValue(block, 'event.timeout');
    const timeout = timeoutRaw ? Number.parseInt(timeoutRaw, 10) : null;
    const onSuccess = getFieldValue(block, 'event.on_success');
    const onFail = getFieldValue(block, 'event.on_fail');

    const hasContent =
      id ||
      title ||
      description ||
      successCriteria.length ||
      npcAppearance.length ||
      timeoutRaw ||
      onSuccess ||
      onFail;
    if (!hasContent) {
      return null;
    }

    return {
      id: id || `event_${index + 1}`,
      title,
      description,
      success_criteria: successCriteria,
      npc_appearance: npcAppearance,
      timeout_turn: Number.isFinite(timeout) ? timeout : null,
      preconditions: [],
      on_success: onSuccess || null,
      on_fail: onFail || null,
    };
  }

  function fillEventBlock(block, data = {}) {
    setFieldValue(block, 'event.id', data.id || '');
    setFieldValue(block, 'event.title', data.title || '');
    setFieldValue(block, 'event.description', data.description || '');
    setFieldValue(block, 'event.npc', formatNpcList(data.npc_appearance || data.npc));
    const timeout = data.timeout_turn ?? data.timeout;
    setFieldValue(block, 'event.timeout', timeout != null ? String(timeout) : '');
    setFieldValue(block, 'event.on_success', data.on_success || '');
    setFieldValue(block, 'event.on_fail', data.on_fail || '');
    fillSuccessCriteria(block, data.success_criteria);
  }

  function readPersonaBlock(block, index) {
    const id = getFieldValue(block, 'persona.id');
    const name = getFieldValue(block, 'persona.name');
    const role = getFieldValue(block, 'persona.role');
    const ageRaw = getFieldValue(block, 'persona.age');
    const gender = getFieldValue(block, 'persona.gender');
    const background = getFieldValue(block, 'persona.background');
    const personality = getFieldValue(block, 'persona.personality');
    const goal = getFieldValue(block, 'persona.goal');
    const speechPattern = getFieldValue(block, 'persona.speech_pattern');
    const emotionInit = getFieldValue(block, 'persona.emotion_init');
    const emotionDuring = splitLines(getFieldValue(block, 'persona.emotion_during'));
    const emotionEnd = getFieldValue(block, 'persona.emotion_end');
    const voiceTags = parseVoiceTags(getFieldValue(block, 'persona.voice_tags'));

    const hasContent =
      id ||
      name ||
      role ||
      ageRaw ||
      gender ||
      background ||
      personality ||
      goal ||
      speechPattern ||
      emotionInit ||
      emotionEnd ||
      voiceTags.length ||
      emotionDuring.length;
    if (!hasContent) {
      return null;
    }

    const age = ageRaw ? Number.parseInt(ageRaw, 10) : null;
    return {
      id: id || `persona_${index + 1}`,
      name,
      role,
      age: Number.isFinite(age) ? age : null,
      gender,
      background,
      personality,
      goal,
      speech_pattern: speechPattern,
      emotion_init: emotionInit,
      emotion_during: emotionDuring,
      emotion_end: emotionEnd,
      voice_tags: voiceTags,
    };
  }

  function fillPersonaBlock(block, data = {}) {
    setFieldValue(block, 'persona.id', data.id || '');
    setFieldValue(block, 'persona.name', data.name || '');
    setFieldValue(block, 'persona.role', data.role || '');
    setFieldValue(block, 'persona.age', data.age != null ? String(data.age) : '');
    setFieldValue(block, 'persona.gender', data.gender || '');
    setFieldValue(block, 'persona.background', data.background || '');
    setFieldValue(block, 'persona.personality', data.personality || '');
    setFieldValue(block, 'persona.goal', data.goal || '');
    setFieldValue(block, 'persona.speech_pattern', data.speech_pattern || '');
    setFieldValue(block, 'persona.emotion_init', data.emotion_init || '');
    setFieldValue(block, 'persona.emotion_during', joinLines(data.emotion_during));
    setFieldValue(block, 'persona.emotion_end', data.emotion_end || '');
    setFieldValue(block, 'persona.voice_tags', formatVoiceTags(data.voice_tags));
  }

  function renumberBlocks(container, label) {
    Array.from(container.children).forEach((block, index) => {
      const title = block.querySelector('[data-block-title]');
      if (title) {
        title.textContent = `${label} #${index + 1}`;
      }
    });
  }

  function splitLines(value) {
    if (!value) {
      return [];
    }
    if (Array.isArray(value)) {
      return value.map((item) => String(item).trim()).filter(Boolean);
    }
    return String(value)
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
  }

  function joinLines(items) {
    if (!Array.isArray(items)) {
      return items || '';
    }
    return items
      .map((item) => (item == null ? '' : String(item).trim()))
      .filter(Boolean)
      .join('\n');
  }

  function parseNpcText(text) {
    if (!text) {
      return [];
    }
    return text
      .split(/[\n,]+/)
      .map((segment) => segment.trim())
      .filter(Boolean)
      .map((segment) => {
        const [rawId, ...rest] = segment.split(':');
        const personaId = (rawId || '').trim();
        const role = rest.join(':').trim();
        if (!personaId) {
          return null;
        }
        return role ? { persona_id: personaId, role } : { persona_id: personaId };
      })
      .filter(Boolean);
  }

  function formatNpcList(list) {
    if (!Array.isArray(list)) {
      return '';
    }
    return list
      .map((entry) => {
        if (!entry) {
          return '';
        }
        if (typeof entry === 'string') {
          return entry.trim();
        }
        const personaId = (entry.persona_id || entry.id || '').trim();
        const role = (entry.role || entry.title || '').trim();
        if (personaId && role) {
          return `${personaId}: ${role}`;
        }
        return personaId || role;
      })
      .filter(Boolean)
      .join('\n');
  }

  function parseVoiceTags(text) {
    if (!text) {
      return [];
    }
    return text
      .split(/[;,]/)
      .map((segment) => segment.trim())
      .filter(Boolean);
  }

  function formatVoiceTags(list) {
    if (Array.isArray(list)) {
      return list.filter(Boolean).join(', ');
    }
    return typeof list === 'string' ? list : '';
  }

  function slugify(value, fallback) {
    const base = (value || '')
      .toString()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
    return base || fallback || 'item';
  }

  function isPlainObject(value) {
    return !!value && typeof value === 'object' && !Array.isArray(value);
  }

  function normalizeSectionPayload(type, payload) {
    if (!payload || typeof payload !== 'object') {
      throw new Error('Tệp JSON không đúng định dạng.');
    }

    if (type === 'skeleton') {
      const skeleton = isPlainObject(payload.skeleton) ? payload.skeleton : payload;
      if (!isPlainObject(skeleton)) {
        throw new Error('File Skeleton JSON không đúng định dạng.');
      }
      return {
        data: skeleton,
        caseId: skeleton.case_id || payload.case_id || '',
      };
    }

    if (type === 'context') {
      const context = isPlainObject(payload.context) ? payload.context : payload;
      if (!isPlainObject(context)) {
        throw new Error('File Context JSON không đúng định dạng.');
      }
      return {
        data: context,
        caseId: context.case_id || payload.case_id || '',
      };
    }

    if (type === 'personas') {
      let container = null;
      if (payload.personas && isPlainObject(payload.personas) && Array.isArray(payload.personas.personas)) {
        container = payload.personas;
      } else if (Array.isArray(payload.personas)) {
        container = { personas: payload.personas };
      } else if (Array.isArray(payload)) {
        container = { personas: payload };
      } else {
        container = payload;
      }

      if (!container || typeof container !== 'object' || !Array.isArray(container.personas)) {
        throw new Error('File Personas JSON không đúng định dạng.');
      }
      return {
        data: container,
        caseId: container.case_id || payload.case_id || '',
      };
    }

    throw new Error('Loại file JSON không được hỗ trợ.');
  }

  function readFileAsText(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        resolve(typeof reader.result === 'string' ? reader.result : '');
      };
      reader.onerror = () => {
        reject(reader.error || new Error('Không thể đọc file JSON.'));
      };
      reader.readAsText(file);
    });
  }

  function getAggregatedCaseId() {
    return (
      controllers.skeleton.getCaseId() ||
      controllers.context.getCaseId() ||
      controllers.personas.getCaseId() ||
      ''
    );
  }

  function syncCaseIds(preferred) {
    const value = preferred || getAggregatedCaseId();
    if (!value) {
      return '';
    }
    controllers.skeleton.setCaseId(value);
    controllers.context.setCaseId(value);
    controllers.personas.setCaseId(value);
    return value;
  }

  function scheduleSaveButtonStateUpdate() {
    if (saveButtonUpdateId != null) {
      cancelAnimationFrame(saveButtonUpdateId);
    }
    saveButtonUpdateId = requestAnimationFrame(() => {
      saveButtonUpdateId = null;
      updateSaveButtonState();
    });
  }

  function updateSaveButtonState() {
    if (!saveCaseButton) {
      return;
    }
    const validation = getValidationState();
    const disabled = !validation.isComplete;
    saveCaseButton.disabled = disabled;
    saveCaseButton.setAttribute('aria-disabled', disabled ? 'true' : 'false');
    saveCaseButton.title = disabled ? 'Bổ sung thông tin trước khi lưu case.' : '';
  }

  function getValidationState() {
    const skeleton = controllers.skeleton.read();
    const context = controllers.context.read();
    const personasPayload = controllers.personas.read();

    const issues = {
      global: [],
      skeleton: [],
      context: [],
      personas: [],
    };

    const resolvedCaseId = skeleton.case_id || context.case_id || personasPayload.case_id;
    if (!resolvedCaseId) {
      issues.global.push('Case ID');
    }

    if (!skeleton.title) {
      issues.skeleton.push('Tên case');
    }
    if (!skeleton.canon_events.length) {
      issues.skeleton.push('Ít nhất 1 Canon Event');
    } else {
      skeleton.canon_events.forEach((event, index) => {
        if (!event.title) {
          issues.skeleton.push(`Canon Event ${index + 1}: tiêu đề`);
        }
        if (!event.description) {
          issues.skeleton.push(`Canon Event ${index + 1}: mô tả`);
        }
      });
    }

    const initialContext = context.initial_context || {};
    const scene = initialContext.scene || {};
    const indexEvent = initialContext.index_event || {};

    if (!context.topic) {
      issues.context.push('Chủ đề case');
    }
    if (!scene.time) {
      issues.context.push('Thời gian trong Scene');
    }
    if (!scene.location) {
      issues.context.push('Địa điểm trong Scene');
    }
    if (!indexEvent.summary) {
      issues.context.push('Tóm tắt sự kiện ban đầu');
    }
    if (!indexEvent.who_first_on_scene) {
      issues.context.push('Ai tiếp cận đầu tiên');
    }

    if (!personasPayload.personas.length) {
      issues.personas.push('Ít nhất 1 persona');
    } else {
      personasPayload.personas.forEach((persona, index) => {
        if (!persona.name) {
          issues.personas.push(`Persona ${index + 1}: tên`);
        }
        if (!persona.role) {
          issues.personas.push(`Persona ${index + 1}: vai trò`);
        }
      });
    }

    const isComplete =
      !issues.global.length &&
      !issues.skeleton.length &&
      !issues.context.length &&
      !issues.personas.length;

    return {
      resolvedCaseId,
      isComplete,
      issues,
    };
  }

  function formatMissingMessages(issues) {
    const parts = [];
    if (issues.global.length) {
      parts.push(`Chung: ${issues.global.join(', ')}`);
    }
    if (issues.skeleton.length) {
      parts.push(`Skeleton: ${issues.skeleton.join(', ')}`);
    }
    if (issues.context.length) {
      parts.push(`Context: ${issues.context.join(', ')}`);
    }
    if (issues.personas.length) {
      parts.push(`Personas: ${issues.personas.join(', ')}`);
    }
    return parts.join(' | ');
  }

  function buildCasePayload() {
    const skeleton = controllers.skeleton.read();
    const context = controllers.context.read();
    const personasPayload = controllers.personas.read();

    const resolvedCaseId = skeleton.case_id || context.case_id || personasPayload.case_id;
    if (!resolvedCaseId) {
      throw new Error('Vui lòng nhập Case ID ở ít nhất một tab trước khi lưu.');
    }

    skeleton.case_id = skeleton.case_id || resolvedCaseId;
    context.case_id = context.case_id || resolvedCaseId;
    personasPayload.case_id = personasPayload.case_id || resolvedCaseId;

    return {
      case_id: resolvedCaseId,
      skeleton,
      context,
      personas: personasPayload,
    };
  }

  function toggleButtonState(button, isLoading) {
    if (!button) {
      return;
    }
    if (isLoading) {
      button.dataset.originalText = button.textContent || '';
      button.textContent = 'Đang lưu...';
      button.disabled = true;
      button.classList.add('cursor-wait', 'opacity-60');
    } else {
      button.disabled = false;
      button.classList.remove('cursor-wait', 'opacity-60');
      if (button.dataset.originalText != null) {
        button.textContent = button.dataset.originalText;
        delete button.dataset.originalText;
      }
    }
  }

  function ensureToastRoot() {
    let root = document.getElementById('toast-root');
    if (!root) {
      root = document.createElement('div');
      root.id = 'toast-root';
      root.className = 'fixed top-4 right-4 z-50 flex flex-col gap-3';
      document.body.appendChild(root);
    }
    return root;
  }

  function showNotification(message, type = 'success') {
    const root = ensureToastRoot();
    const toast = document.createElement('div');
    toast.className =
      'rounded-xl px-4 py-3 text-sm font-semibold shadow-lg backdrop-blur ' +
      (type === 'error'
        ? 'bg-rose-600/90 text-white'
        : type === 'info'
        ? 'bg-slate-800/90 text-white'
        : 'bg-emerald-600/90 text-white');
    toast.textContent = message;
    root.appendChild(toast);
    requestAnimationFrame(() => {
      toast.classList.add('transition', 'duration-200');
    });
    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-1');
      toast.addEventListener(
        'transitionend',
        () => {
          toast.remove();
        },
        { once: true }
      );
    }, 2800);
  }
});
