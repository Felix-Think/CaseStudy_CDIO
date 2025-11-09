
    document.addEventListener("DOMContentLoaded", () => {
      const mergeMaps = (...maps) => Object.assign({}, ...maps);

      const EVENT_LABELS = {
        "Mã sự kiện": "event.id",
        "Tiêu đề": "event.title",
        "Mô tả chi tiết": "event.description",
        "Success Criteria": "event.success_criteria",
        "NPC xuất hiện": "event.npc",
        "Timeout (lượt)": "event.timeout",
        "On Success": "event.on_success",
        "On Fail": "event.on_fail",
      };

      const RESOURCE_LABELS = {
        "Tên nhóm": "context.resource.label",
        "Ghi chú (tùy chọn)": "context.resource.note",
        "Danh sách nguồn lực": "context.resource.items",
      };

      const PERSONA_ITEM_LABELS = {
        "Persona ID": "persona.id",
        "Tên nhân vật": "persona.name",
        "Vai trò": "persona.role",
        "Tuổi": "persona.age",
        "Giới tính": "persona.gender",
        "Lý lịch / hoàn cảnh": "persona.background",
        "Tính cách": "persona.personality",
        "Mục tiêu": "persona.goal",
        "Speech pattern": "persona.speech_pattern",
        "Emotion ban đầu": "persona.emotion_init",
        "Emotion kết thúc": "persona.emotion_end",
        "Voice tags": "persona.voice_tags",
        "Emotion trong quá trình": "persona.emotion_during",
      };

      const skeletonPanel = document.querySelector('[data-panel="skeleton"]');
      const contextPanel = document.querySelector('[data-panel="context"]');
      const personasPanel = document.querySelector('[data-panel="personas"]');
      const skeletonEventTemplate = document.getElementById('skeleton-event-template');
      const resourceTemplate = document.getElementById('resource-template');
      const personaTemplate = document.getElementById('persona-template');

      const mapLabelsToFields = (root, map) => {
        if (!root) return;
        const labels = root.querySelectorAll('label');
        labels.forEach((label) => {
          const key = map[label.textContent.trim()];
          if (!key) return;
          const control = label.querySelector('input, textarea');
          if (control) {
            control.dataset.fieldKey = key;
          }
        });
      };

      mapLabelsToFields(
        skeletonPanel,
        mergeMaps(
          {
            'Case ID': 'skeleton.case_id',
            'Tên case': 'skeleton.title',
          },
          EVENT_LABELS,
        ),
      );
      if (skeletonEventTemplate) {
        mapLabelsToFields(skeletonEventTemplate.content, EVENT_LABELS);
      }
      mapLabelsToFields(
        contextPanel,
        mergeMaps(
          {
            'Case ID': 'context.case_id',
            'Chủ đề case': 'context.topic',
            'Thời gian': 'context.scene.time',
            'Thời tiết': 'context.scene.weather',
            'Vị trí': 'context.scene.location',
            'Mức độ ồn & ghi chú khác': 'context.scene.noise',
            'Tóm tắt sự kiện': 'context.index_event.summary',
            'Tình trạng hiện tại': 'context.index_event.current_state',
            'Ai tiếp cận đầu tiên': 'context.index_event.who_first',
            'Ràng buộc hiện trường': 'context.constraints',
            'Chính sách & an toàn': 'context.policies',
            'Đơn vị bàn giao': 'context.handover',
            'Trạng thái thành công cuối cùng': 'context.success_state',
          },
          RESOURCE_LABELS,
        ),
      );
      if (resourceTemplate) {
        mapLabelsToFields(resourceTemplate.content, RESOURCE_LABELS);
      }
      mapLabelsToFields(
        personasPanel,
        mergeMaps(
          {
            'Case ID': 'personas.case_id',
            'Số lượng persona (tham khảo)': 'personas.count',
          },
          PERSONA_ITEM_LABELS,
        ),
      );
      if (personaTemplate) {
        mapLabelsToFields(personaTemplate.content, PERSONA_ITEM_LABELS);
      }

      const tabButtons = document.querySelectorAll('[data-tab]');
      const panels = document.querySelectorAll('[data-panel]');
      const ACTIVE_BUTTON_CLASSES = ['bg-primary-600', 'text-white', 'border-primary-600', 'hover:bg-primary-500', 'hover:text-white', 'hover:border-primary-600', 'shadow-md'];
      const INACTIVE_BUTTON_CLASSES = ['bg-white', 'text-primary-600', 'hover:text-primary-700', 'hover:border-primary-300'];

      const activateTab = (tabId) => {
        tabButtons.forEach((button) => {
          const isActive = button.dataset.tab === tabId;
          if (isActive) {
            button.classList.add(...ACTIVE_BUTTON_CLASSES);
            button.classList.remove(...INACTIVE_BUTTON_CLASSES);
            button.setAttribute('aria-selected', 'true');
            button.setAttribute('tabindex', '0');
          } else {
            button.classList.remove(...ACTIVE_BUTTON_CLASSES);
            button.classList.add(...INACTIVE_BUTTON_CLASSES);
            button.setAttribute('aria-selected', 'false');
            button.setAttribute('tabindex', '-1');
          }
        });

        panels.forEach((panel) => {
          if (panel.dataset.panel === tabId) {
            panel.classList.remove('hidden');
          } else {
            panel.classList.add('hidden');
          }
        });
      };

      tabButtons.forEach((button) => {
        button.addEventListener('click', () => activateTab(button.dataset.tab));
      });
      activateTab('skeleton');

      document.querySelectorAll('[data-next-tab]').forEach((button) => {
        button.addEventListener('click', () => {
          if (button.dataset.nextTab) {
            activateTab(button.dataset.nextTab);
          }
        });
      });

      document.querySelectorAll('[data-prev-tab]').forEach((button) => {
        button.addEventListener('click', () => {
          if (button.dataset.prevTab) {
            activateTab(button.dataset.prevTab);
          }
        });
      });

      const selectField = (root, key) => (root ? root.querySelector([data-field-key=""]) : null);
      const normalizeLines = (value) => {
        if (!value) return [];
        if (Array.isArray(value)) return value.map((item) => String(item)).filter(Boolean);
        return String(value)
          .split(/
?
/)
          .map((item) => item.trim())
          .filter(Boolean);
      };

      const setFieldValue = (root, key, rawValue) => {
        const field = selectField(root, key);
        if (!field) return;
        let value = '';
        if (Array.isArray(rawValue)) {
          value = rawValue.filter((item) => item != null && item !== '').join('
');
        } else if (rawValue !== undefined && rawValue !== null) {
          value = String(rawValue);
        }
        field.value = value;
        field.dispatchEvent(new Event('input', { bubbles: true }));
      };

      const getFieldValue = (root, key) => {
        const field = selectField(root, key);
        return field ? field.value.trim() : '';
      };

      const setLines = (root, key, value) => {
        setFieldValue(root, key, normalizeLines(value));
      };

      const getLines = (root, key) => normalizeLines(getFieldValue(root, key));

      const parseNPC = (raw) => {
        if (!raw) return [];
        return raw
          .split(/[
,]+/)
          .map((segment) => {
            const [personaId, ...rest] = segment.split(':');
            const id = (personaId || '').trim();
            const role = rest.join(':').trim();
            if (!id) return null;
            return role ? { persona_id: id, role } : { persona_id: id };
          })
          .filter(Boolean);
      };

      const formatNpcAppearance = (list) => {
        if (!Array.isArray(list)) return '';
        return list
          .map((entry) => {
            if (!entry) return '';
            if (typeof entry === 'string') return entry.trim();
            const id = (entry.persona_id || entry.id || '').trim();
            const role = (entry.role || entry.title || '').trim();
            if (id && role) return ${id}: ;
            return id || role;
          })
          .filter(Boolean)
          .join('
');
      };

      const parseVoiceTags = (raw) => {
        if (!raw) return [];
        return raw
          .split(',')
          .map((tag) => tag.trim())
          .filter(Boolean);
      };

      const formatVoiceTags = (tags) => {
        if (Array.isArray(tags)) {
          return tags.filter(Boolean).join(', ');
        }
        return typeof tags === 'string' ? tags : '';
      };

      const parseInteger = (raw) => {
        if (!raw) return undefined;
        const value = Number(raw);
        return Number.isFinite(value) ? value : undefined;
      };

      const skeletonForm = skeletonPanel.querySelector('form');
      const contextForm = contextPanel.querySelector('form');
      const personasForm = personasPanel.querySelector('form');

      const skeletonEventsContainer = skeletonPanel.querySelector('[data-skeleton-events]');
      const contextResourceList = contextPanel.querySelector('[data-resource-list]');
      const personaList = personasPanel.querySelector('[data-persona-list]');

      const ensureList = (container, template, desiredCount, initCallback) => {
        if (!container || !template) return [];
        const target = Math.max(desiredCount, 1);
        while (container.children.length > target) {
          container.removeChild(container.lastElementChild);
        }
        while (container.children.length < target) {
          const clone = template.content.firstElementChild.cloneNode(true);
          container.appendChild(clone);
          if (typeof initCallback === 'function') {
            initCallback(clone);
          }
        }
        return Array.from(container.children);
      };

      const initEventBlock = (block) => {
        mapLabelsToFields(block, EVENT_LABELS);
        const removeBtn = block.querySelector('[data-remove-event]');
        if (removeBtn) {
          removeBtn.addEventListener('click', () => {
            if (skeletonEventsContainer.children.length === 1) {
              Array.from(block.querySelectorAll('input, textarea')).forEach((field) => {
                field.value = '';
              });
              updateSaveButtonState();
              return;
            }
            block.remove();
            updateSaveButtonState();
          });
        }
      };

      const initResourceBlock = (block) => {
        mapLabelsToFields(block, RESOURCE_LABELS);
        const removeBtn = block.querySelector('[data-remove-resource]');
        if (!removeBtn) return;
        removeBtn.addEventListener('click', () => {
          if (contextResourceList.children.length === 1) {
            Array.from(block.querySelectorAll('input, textarea')).forEach((field) => {
              field.value = '';
            });
            updateSaveButtonState();
            return;
          }
          block.remove();
          updateSaveButtonState();
        });
      };

      const initPersonaItem = (item) => {
        mapLabelsToFields(item, PERSONA_ITEM_LABELS);
        const removeBtn = item.querySelector('[data-remove-persona]');
        if (!removeBtn) return;
        removeBtn.addEventListener('click', () => {
          if (personaList.children.length === 1) {
            Array.from(item.querySelectorAll('input, textarea')).forEach((field) => {
              field.value = '';
            });
            updateSaveButtonState();
            return;
          }
          item.remove();
          updateSaveButtonState();
        });
      };

      skeletonEventsContainer.querySelectorAll('[data-event-block]').forEach(initEventBlock);
      contextResourceList.querySelectorAll('[data-resource-block]').forEach(initResourceBlock);
      personaList.querySelectorAll('[data-persona-item]').forEach(initPersonaItem);

      const addEventBtn = skeletonPanel.querySelector('[data-add-event]');
      if (addEventBtn && skeletonEventTemplate) {
        addEventBtn.addEventListener('click', () => {
          const clone = skeletonEventTemplate.content.firstElementChild.cloneNode(true);
          skeletonEventsContainer.appendChild(clone);
          initEventBlock(clone);
          updateSaveButtonState();
        });
      }
...

  <style>
    :root {
      font-family: Arial, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    body,
    input,
    textarea,
    button,
    select {
      font-family: inherit;
    }
  </style>
  <link rel="icon" type="image/x-icon" href="/favicon.ico" />
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body class="min-h-screen bg-slate-50 text-slate-800 font-sans">
  <div class="relative flex min-h-screen flex-col">
    <div class="absolute inset-0 -z-10 bg-gradient-to-br from-primary-50 via-white to-slate-100"></div>
    <header class="sticky top-0 z-40 border-b border-slate-100 bg-white/80 backdrop-blur">
      <div class="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <a href="/" class="text-sm font-semibold text-primary-600 transition hover:text-primary-500">Quay lại trang chính</a>
        <span class="text-sm text-slate-500">Tổng hợp nội dung từ JSON</span>
      </div>
    </header>
    <main class="flex-1 px-6 py-16">
      <div class="mx-auto flex max-w-6xl flex-col gap-10">
        <header class="space-y-4 border-b border-slate-100 pb-6">
          <h1 class="text-3xl font-semibold text-slate-900">Trang Nhập Case</h1>
          <p class="text-sm text-slate-600">
            Giao diện này giúp bạn chuẩn bị dữ liệu cho case mới với ba phần chính: Skeleton, Context và Personas.
          </p>
          <p class="text-xs text-slate-500">
            Chọn thẻ tương ứng để nhập dữ liệu. Nội dung chỉ lưu trên trình duyệt trừ khi bạn tự xử lý tải lên máy chủ.
          </p>
        </header>

        <section
          class="rounded-3xl border-2 border-dashed border-primary-200 bg-white/80 p-8 text-sm text-slate-600 transition duration-200 focus-within:border-primary-300"
          data-json-import-wrapper
        >
          <div class="flex flex-col items-center gap-4 text-center">
            <span class="inline-flex items-center gap-2 rounded-full bg-primary-100 px-4 py-1 text-xs font-semibold uppercase tracking-wide text-primary-700">
              Nhap du lieu tu file JSON
            </span>
            <p class="text-base font-semibold text-slate-900">
              Chon lan luot 3 file: Skeleton, Context va Personas
            </p>
            <p class="text-xs text-slate-500 max-w-xl">
              Moi file duoc xu ly hoan toan tren trinh duyet. Noi dung se tu dong dien vao tung tab va ban co the chinh sua truoc khi luu case.
            </p>
          </div>
          <div class="mt-6 grid gap-4 md:grid-cols-3" data-json-import-grid>
            <div
              class="group flex cursor-pointer flex-col items-center gap-3 rounded-2xl border-2 border-dashed border-primary-100 bg-white/70 p-6 text-center transition duration-200 focus-within:border-primary-400 focus-within:shadow hover:border-primary-300 hover:bg-primary-50"
              data-json-section="skeleton"
              tabindex="0"
              role="button"
              aria-label="Nhap file Skeleton JSON"
            >
              <input type="file" accept="application/json" class="hidden" data-json-file-input="skeleton" />
              <span class="text-xs font-semibold uppercase tracking-wide text-primary-700">Skeleton JSON</span>
              <p class="text-sm font-semibold text-slate-900">Keo tha hoac bam de chon skeleton.json</p>
              <p class="max-w-[16rem] text-xs text-slate-500" data-json-status="skeleton">Chua chon file</p>
              <div class="flex flex-wrap items-center justify-center gap-2">
                <button
                  type="button"
                  data-json-import-button="skeleton"
                  class="rounded-full bg-primary-600 px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                >
                  Chon file
                </button>
                <button
                  type="button"
                  data-json-clear-button="skeleton"
                  class="rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-500 transition hover:border-slate-300 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-100"
                >
                  Xoa
                </button>
              </div>
            </div>
            <div
              class="group flex cursor-pointer flex-col items-center gap-3 rounded-2xl border-2 border-dashed border-primary-100 bg-white/70 p-6 text-center transition duration-200 focus-within:border-primary-400 focus-within:shadow hover:border-primary-300 hover:bg-primary-50"
              data-json-section="context"
              tabindex="0"
              role="button"
              aria-label="Nhap file Context JSON"
            >
              <input type="file" accept="application/json" class="hidden" data-json-file-input="context" />
              <span class="text-xs font-semibold uppercase tracking-wide text-primary-700">Context JSON</span>
              <p class="text-sm font-semibold text-slate-900">Keo tha hoac bam de chon context.json</p>
              <p class="max-w-[16rem] text-xs text-slate-500" data-json-status="context">Chua chon file</p>
              <div class="flex flex-wrap items-center justify-center gap-2">
                <button
                  type="button"
                  data-json-import-button="context"
                  class="rounded-full bg-primary-600 px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                >
                  Chon file
                </button>
                <button
                  type="button"
                  data-json-clear-button="context"
                  class="rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-500 transition hover:border-slate-300 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-100"
                >
                  Xoa
                </button>
              </div>
            </div>
            <div
              class="group flex cursor-pointer flex-col items-center gap-3 rounded-2xl border-2 border-dashed border-primary-100 bg-white/70 p-6 text-center transition duration-200 focus-within:border-primary-400 focus-within:shadow hover:border-primary-300 hover:bg-primary-50"
              data-json-section="personas"
              tabindex="0"
              role="button"
              aria-label="Nhap file Personas JSON"
            >
              <input type="file" accept="application/json" class="hidden" data-json-file-input="personas" />
              <span class="text-xs font-semibold uppercase tracking-wide text-primary-700">Personas JSON</span>
              <p class="text-sm font-semibold text-slate-900">Keo tha hoac bam de chon personas.json</p>
              <p class="max-w-[16rem] text-xs text-slate-500" data-json-status="personas">Chua chon file</p>
              <div class="flex flex-wrap items-center justify-center gap-2">
                <button
                  type="button"
                  data-json-import-button="personas"
                  class="rounded-full bg-primary-600 px-4 py-1.5 text-xs font-semibold text-white transition hover:bg-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                >
                  Chon file
                </button>
                <button
                  type="button"
                  data-json-clear-button="personas"
                  class="rounded-full border border-slate-200 px-4 py-1.5 text-xs font-semibold text-slate-500 transition hover:border-slate-300 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-primary-100"
                >
                  Xoa
                </button>
              </div>
            </div>
          </div>
        </section>

        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex flex-wrap gap-3" role="tablist" aria-label="Biểu mẫu nhập case">
            <button
              type="button"
              role="tab"
              id="tab-skeleton"
              data-tab="skeleton"
              aria-controls="panel-skeleton"
              aria-selected="true"
              class="tab-trigger inline-flex items-center gap-2 rounded-full border border-primary-200 px-5 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-primary-100"
            >
              Nhập Skeleton
            </button>
            <button
              type="button"
              role="tab"
              id="tab-context"
              data-tab="context"
              aria-controls="panel-context"
              aria-selected="false"
              class="tab-trigger inline-flex items-center gap-2 rounded-full border border-primary-200 px-5 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-primary-100"
            >
              Nhập Context
            </button>
            <button
              type="button"
              role="tab"
              id="tab-personas"
              data-tab="personas"
              aria-controls="panel-personas"
              aria-selected="false"
              class="tab-trigger inline-flex items-center gap-2 rounded-full border border-primary-200 px-5 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-primary-100"
            >
              Nhập Personas
            </button>
          </div>
          <button
            type="button"
            id="save-case-button"
            class="rounded-full border border-slate-200 bg-white px-5 py-2 text-sm font-semibold text-slate-400 transition focus:outline-none focus:ring-2 focus:ring-primary-100 cursor-not-allowed"
            disabled
          >
            Lưu Case
          </button>
        </div>

        <section
          id="panel-skeleton"
          role="tabpanel"
          aria-labelledby="tab-skeleton"
          data-panel="skeleton"
          class="tab-panel rounded-3xl border border-slate-100 bg-white/80 p-8 shadow-card"
        >
          <form data-prevent-submit class="space-y-6">
            <div class="grid gap-4 md:grid-cols-2">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Case ID
                <input
                  type="text"
                  placeholder="ví dụ: case_training_001" data-field="skeleton.case_id"
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white/70 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                />
              </label>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Tên case
                <input
                  type="text"
                  placeholder="ví dụ: Huấn luyện xử lý sự cố khẩn cấp" data-field="skeleton.title"
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white/70 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                />
              </label>
            </div>

            <div>
              <div class="flex flex-wrap items-center gap-3">
                <h2 class="text-base font-semibold text-slate-900">Danh sách Canon Event</h2>
              </div>
              <p class="mt-2 text-xs text-slate-500">
                Điền từng bước theo trình tự của case. Có thể thêm nhiều event và chỉnh timeout, NPC, nhánh chuyển tiếp.
              </p>
              <div class="mt-4 space-y-4" data-skeleton-events>
                <div data-event-block class="rounded-2xl border border-slate-100 bg-white/60 p-6 shadow-inner">
                  <div class="flex flex-wrap items-center justify-between gap-3">
                    <h3 class="text-sm font-semibold text-slate-900">Canon Event</h3>
                    <button
                      type="button"
                      data-remove-event
                      class="text-xs font-semibold text-slate-500 transition hover:text-primary-600"
                    >
                      Xóa
                    </button>
                  </div>
                  <div class="mt-4 grid gap-4 md:grid-cols-2">
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Mã sự kiện
                      <input
                        type="text"
                        placeholder="ví dụ: CE1"
                        class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      />
                    </label>
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Tiêu đề
                      <input
                        type="text"
                        placeholder="ví dụ: Đánh giá ban đầu hiện trường"
                        class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      />
                    </label>
                  </div>
                  <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Mô tả chi tiết
                    <textarea
                      rows="3"
                      placeholder="Mô tả ngắn gọn về nhiệm vụ của event."
                      class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                    ></textarea>
                  </label>
                  <div class="mt-4 grid gap-4 md:grid-cols-2">
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Success Criteria
                      <textarea
                        rows="3"
                        placeholder="Ghi từng tiêu chí trên một dòng."
                        class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      ></textarea>
                    </label>
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      NPC xuất hiện
                      <input
                        type="text"
                        placeholder="ví dụ: P1: Điều phối viên, P2: Người hỗ trợ"
                        class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      />
                    </label>
                  </div>
                  <div class="mt-4 grid gap-4 md:grid-cols-3">
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Timeout (lượt)
                      <input
                        type="number"
                        min="0"
                        placeholder="ví dụ: 3"
                        class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      />
                    </label>
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      On Success
                      <input
                        type="text"
                        placeholder="ví dụ: CE2"
                        class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      />
                    </label>
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      On Fail
                      <input
                        type="text"
                        placeholder="ví dụ: CE1_RETRY"
                        class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      />
                    </label>
                  </div>
                </div>
              </div>
              <div class="mt-4 flex justify-end">
                <button
                  type="button"
                  data-add-event
                  class="inline-flex items-center gap-2 rounded-full border border-primary-200 bg-primary-50 px-4 py-2 text-xs font-semibold text-primary-600 transition hover:border-primary-400 hover:bg-primary-100"
                >
                  + Thêm event
                </button>
              </div>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
              <button
                type="reset"
                class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-primary-200 hover:text-primary-600"
              >
                Reset
              </button>
              <button
                type="button"
                data-next-tab="context"
                class="rounded-full bg-primary-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-500"
              >
                Sang tab Context
              </button>
            </div>
          </form>
        </section>

        <section
          id="panel-context"
          role="tabpanel"
          aria-labelledby="tab-context"
          data-panel="context"
          class="tab-panel hidden rounded-3xl border border-slate-100 bg-white/80 p-8 shadow-card"
        >
          <form data-prevent-submit class="space-y-6">
            <div class="grid gap-4 md:grid-cols-2">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Case ID
                <input
                  type="text"
                  placeholder="ví dụ: case_training_001"
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white/70 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                />
              </label>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Chủ đề case
                <input
                  type="text"
                  placeholder="ví dụ: Ứng phó sự cố vận hành"
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white/70 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                />
              </label>
            </div>

            <fieldset class="space-y-4 rounded-2xl border border-slate-100 bg-white/60 p-6 shadow-inner">
              <legend class="text-sm font-semibold uppercase tracking-wide text-slate-500">Thông tin hiện trường</legend>
              <div class="grid gap-4 md:grid-cols-2">
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Thời gian
                  <input
                    type="text"
                    placeholder="ví dụ: 14:30"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  />
                </label>
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Thời tiết
                  <input
                    type="text"
                    placeholder="ví dụ: Mưa nhẹ, sàn trơn"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  />
                </label>
                <label class="md:col-span-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Vị trí
                  <textarea
                    rows="2"
                    placeholder="ví dụ: Khu vực sản xuất chính, nhiều người qua lại."
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  ></textarea>
                </label>
                <label class="md:col-span-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Mức độ ồn &amp; ghi chú khác
                  <textarea
                    rows="2"
                    placeholder="ví dụ: Ồn ào do máy móc, liên tục có thông báo nội bộ."
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  ></textarea>
                </label>
              </div>
            </fieldset>

            <fieldset class="space-y-4 rounded-2xl border border-slate-100 bg-white/60 p-6 shadow-inner">
              <legend class="text-sm font-semibold uppercase tracking-wide text-slate-500">Trạng thái ban đầu</legend>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Tóm tắt sự kiện
                <textarea
                  rows="2"
                  placeholder="ví dụ: Phát hiện sự cố bất thường, cần phản ứng khẩn cấp."
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                ></textarea>
              </label>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Tình trạng hiện tại
                <textarea
                  rows="3"
                  placeholder="ví dụ: Nạn nhân mệt mỏi, dấu hiệu sinh tồn không ổn định."
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                ></textarea>
              </label>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Ai tiếp cận đầu tiên
                <input
                  type="text"
                  placeholder="ví dụ: Nhân viên trực ca"
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                />
              </label>
            </fieldset>

            <fieldset class="space-y-4 rounded-2xl border border-slate-100 bg-white/60 p-6 shadow-inner">
              <legend class="text-sm font-semibold uppercase tracking-wide text-slate-500">Nguồn lực sẵn có</legend>
              <p class="text-xs text-slate-500">
                Tạo các nhóm nguồn lực phù hợp với case. Mỗi nhóm có thể đại diện cho thiết bị, nhân lực hoặc bất kỳ tài nguyên nào khác.
              </p>
              <div class="space-y-4" data-resource-list>
                <div data-resource-block class="rounded-2xl border border-slate-100 bg-white/70 p-6 shadow-inner">
                  <div class="flex flex-wrap items-center justify-between gap-3">
                    <h3 class="text-sm font-semibold text-slate-900">Nhóm nguồn lực</h3>
                    <button
                      type="button"
                      data-remove-resource
                      class="text-xs font-semibold text-slate-500 transition hover:text-primary-600"
                    >
                      Xóa
                    </button>
                  </div>
                  <div class="mt-4 grid gap-4 md:grid-cols-2">
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Tên nhóm
                      <input
                        type="text"
                        placeholder="ví dụ: Thiết bị hỗ trợ"
                        class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      />
                    </label>
                    <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Ghi chú (tùy chọn)
                      <input
                        type="text"
                        placeholder="ví dụ: Đặt gần cửa ra vào"
                        class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                      />
                    </label>
                  </div>
                  <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Danh sách nguồn lực
                    <textarea
                      rows="3"
                      placeholder="Ghi từng nguồn lực trên một dòng."
                      class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                    ></textarea>
                  </label>
                </div>
              </div>
              <div class="mt-4 flex justify-end">
                <button
                  type="button"
                  data-add-resource
                  class="inline-flex items-center gap-2 rounded-full border border-primary-200 bg-primary-50 px-4 py-2 text-xs font-semibold text-primary-600 transition hover:border-primary-400 hover:bg-primary-100"
                >
                  + Thêm nhóm nguồn lực
                </button>
              </div>
            </fieldset>

            <fieldset class="space-y-4 rounded-2xl border border-slate-100 bg-white/60 p-6 shadow-inner">
              <legend class="text-sm font-semibold uppercase tracking-wide text-slate-500">Ràng buộc &amp; chính sách</legend>
              <div class="grid gap-4 md:grid-cols-2">
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Ràng buộc hiện trường
                  <textarea
                    rows="3"
                    placeholder="ví dụ: Không gian hạn chế&#10;Thiết bị thiếu&#10;Áp lực thời gian"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  ></textarea>
                </label>
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Chính sách &amp; an toàn
                  <textarea
                    rows="3"
                    placeholder="ví dụ: Ưu tiên an toàn đội ngũ&#10;Tuân thủ quy trình tiêu chuẩn&#10;Bảo mật thông tin"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  ></textarea>
                </label>
              </div>
            </fieldset>

            <fieldset class="space-y-4 rounded-2xl border border-slate-100 bg-white/60 p-6 shadow-inner">
              <legend class="text-sm font-semibold uppercase tracking-wide text-slate-500">Bàn giao &amp; kết thúc</legend>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Đơn vị bàn giao
                <input
                  type="text"
                  placeholder="ví dụ: Đội phản ứng chuyên trách"
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                />
              </label>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Trạng thái thành công cuối cùng
                <textarea
                  rows="3"
                  placeholder="ví dụ: Nạn nhân ổn định, thông tin bàn giao đầy đủ, bên liên quan được trấn an."
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                ></textarea>
              </label>
            </fieldset>

            <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
              <button
                type="reset"
                class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-primary-200 hover:text-primary-600"
              >
                Reset
              </button>
              <div class="flex items-center gap-3">
                <button
                  type="button"
                  data-prev-tab="skeleton"
                  class="rounded-full border border-primary-200 px-4 py-2 text-sm font-semibold text-primary-600 transition hover:bg-primary-50"
                >
                  Quay lại Skeleton
                </button>
                <button
                  type="button"
                  data-next-tab="personas"
                  class="rounded-full bg-primary-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-500"
                >
                  Sang tab Personas
                </button>
              </div>
            </div>
        </div>
          </form>
        </section>

        <section
          id="panel-personas"
          role="tabpanel"
          aria-labelledby="tab-personas"
          data-panel="personas"
          class="tab-panel hidden rounded-3xl border border-slate-100 bg-white/80 p-8 shadow-card"
        >
          <form data-prevent-submit class="space-y-6">
            <div class="grid gap-4 md:grid-cols-2">
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Case ID
                <input
                  type="text"
                  placeholder="ví dụ: case_training_001"
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white/70 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                />
              </label>
              <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Số lượng persona (tham khảo)
                <input
                  type="number"
                  min="1"
                  placeholder="ví dụ: 4"
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white/70 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                />
              </label>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <h2 class="text-base font-semibold text-slate-900">Danh sách Personas</h2>
            </div>
            <p class="text-xs text-slate-500">
              Mỗi persona đại diện cho một nhân vật tham gia tình huống. Bạn có thể thêm hoặc xóa nhưng luôn dựa trên cấu trúc JSON gốc.
            </p>

            <div class="space-y-4" data-persona-list>
              <div data-persona-item class="rounded-2xl border border-slate-100 bg-white/60 p-6 shadow-inner">
                <div class="flex flex-wrap items-center justify-between gap-3">
                  <h3 class="text-sm font-semibold text-slate-900">Persona</h3>
                  <button
                    type="button"
                    data-remove-persona
                    class="text-xs font-semibold text-slate-500 transition hover:text-primary-600"
                  >
                    Xóa
                  </button>
                </div>
                <div class="mt-4 grid gap-4 md:grid-cols-2">
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Persona ID
                  <input
                    type="text"
                    placeholder="ví dụ: P1"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  />
                </label>
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Tên nhân vật
                  <input
                    type="text"
                    placeholder="ví dụ: Điều phối viên hiện trường"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  />
                </label>
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Vai trò
                  <input
                    type="text"
                    placeholder="ví dụ: Giám sát sự cố"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  />
                </label>
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Tuổi
                  <input
                    type="number"
                    min="0"
                    placeholder="ví dụ: 32"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  />
                </label>
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Giới tính
                  <input
                    type="text"
                    placeholder="ví dụ: Nam/Nữ/Khác"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  />
                </label>
              </div>
              <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Lý lịch / hoàn cảnh
                <textarea
                  rows="3"
                  placeholder="ví dụ: Kinh nghiệm làm việc, điểm mạnh, hạn chế."
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                ></textarea>
              </label>
              <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Tính cách
                <textarea
                  rows="3"
                  placeholder="ví dụ: Bình tĩnh, quyết đoán, nhạy cảm."
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                ></textarea>
              </label>
              <div class="mt-4 grid gap-4 md:grid-cols-2">
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Mục tiêu
                  <textarea
                    rows="3"
                    placeholder="ví dụ: Đảm bảo an toàn đội ngũ, hoàn thành nhiệm vụ."
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  ></textarea>
                </label>
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Speech pattern
                  <textarea
                    rows="3"
                    placeholder="ví dụ: Nói nhanh, nhiều thuật ngữ; hoặc chậm rãi, trấn an."
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  ></textarea>
                </label>
              </div>
              <div class="mt-4 grid gap-4 md:grid-cols-3">
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Emotion ban đầu
                  <input
                    type="text"
                    placeholder="ví dụ: Lo lắng"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  />
                </label>
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Emotion kết thúc
                  <input
                    type="text"
                    placeholder="ví dụ: Bình tĩnh"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  />
                </label>
                <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Voice tags
                  <input
                    type="text"
                    placeholder="ví dụ: mentor, calm"
                    class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                  />
                </label>
              </div>
              <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
                Emotion trong quá trình
                <textarea
                  rows="3"
                  placeholder="ví dụ: căng thẳng&#10;tập trung&#10;trấn an"
                  class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
                ></textarea>
                </label>
              </div>
            </div>

            <div class="mt-4 flex justify-end">
              <button
                type="button"
                data-add-persona
                class="inline-flex items-center gap-2 rounded-full border border-primary-200 bg-primary-50 px-4 py-2 text-xs font-semibold text-primary-600 transition hover:border-primary-400 hover:bg-primary-100"
              >
                + Thêm persona
              </button>
            </div>

            <div class="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
              <button
                type="reset"
                class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-600 transition hover:border-primary-200 hover:text-primary-600"
              >
                Reset
              </button>
              <button
                type="button"
                data-prev-tab="context"
                class="rounded-full border border-primary-200 px-4 py-2 text-sm font-semibold text-primary-600 transition hover:bg-primary-50"
              >
                Quay lại Context
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  </div>

  <template id="resource-template">
    <div data-resource-block class="rounded-2xl border border-slate-100 bg-white/70 p-6 shadow-inner">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h3 class="text-sm font-semibold text-slate-900">Nhóm nguồn lực</h3>
        <button
          type="button"
          data-remove-resource
          class="text-xs font-semibold text-slate-500 transition hover:text-primary-600"
        >
          Xóa
        </button>
      </div>
      <div class="mt-4 grid gap-4 md:grid-cols-2">
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Tên nhóm
          <input
            type="text"
            placeholder="ví dụ: Nhân lực hỗ trợ"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Ghi chú (tùy chọn)
          <input
            type="text"
            placeholder="ví dụ: Liên hệ trực ca"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
      </div>
      <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
        Danh sách nguồn lực
        <textarea
          rows="3"
          placeholder="Ghi từng nguồn lực trên một dòng."
          class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
        ></textarea>
      </label>
    </div>
  </template>

  <template id="skeleton-event-template">
    <div data-event-block class="rounded-2xl border border-slate-100 bg-white/60 p-6 shadow-inner">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h3 class="text-sm font-semibold text-slate-900">Canon Event</h3>
        <button
          type="button"
          data-remove-event
          class="text-xs font-semibold text-slate-500 transition hover:text-primary-600"
        >
          Xóa
        </button>
      </div>
      <div class="mt-4 grid gap-4 md:grid-cols-2">
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Mã sự kiện
          <input
            type="text"
            placeholder="ví dụ: CE2"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Tiêu đề
          <input
            type="text"
            placeholder="ví dụ: Điều phối phản ứng"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
      </div>
      <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
        Mô tả chi tiết
        <textarea
          rows="3"
          placeholder="Mô tả ngắn gọn về nhiệm vụ của event."
          class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
        ></textarea>
      </label>
      <div class="mt-4 grid gap-4 md:grid-cols-2">
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Success Criteria
          <textarea
            rows="3"
            placeholder="Ghi từng tiêu chí trên một dòng."
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          ></textarea>
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          NPC xuất hiện
          <input
            type="text"
            placeholder="ví dụ: P2: Người giám sát, P3: Nhân sự hỗ trợ"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
      </div>
      <div class="mt-4 grid gap-4 md:grid-cols-3">
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Timeout (lượt)
          <input
            type="number"
            min="0"
            placeholder="ví dụ: 3"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          On Success
          <input
            type="text"
            placeholder="ví dụ: CE3"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          On Fail
          <input
            type="text"
            placeholder="ví dụ: CE2_RETRY"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
      </div>
    </div>
  </template>

  <template id="persona-template">
    <div data-persona-item class="rounded-2xl border border-slate-100 bg-white/60 p-6 shadow-inner">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h3 class="text-sm font-semibold text-slate-900">Persona</h3>
        <button
          type="button"
          data-remove-persona
          class="text-xs font-semibold text-slate-500 transition hover:text-primary-600"
        >
          Xóa
        </button>
      </div>
      <div class="mt-4 grid gap-4 md:grid-cols-2">
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Persona ID
          <input
            type="text"
            placeholder="ví dụ: P2"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Tên nhân vật
          <input
            type="text"
            placeholder="ví dụ: Điều phối viên phụ"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Vai trò
          <input
            type="text"
            placeholder="ví dụ: Hỗ trợ hậu cần"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Tuổi
          <input
            type="number"
            min="0"
            placeholder="ví dụ: 35"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Giới tính
          <input
            type="text"
            placeholder="ví dụ: Nam/Nữ/Khác"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
      </div>
      <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
        Lý lịch / hoàn cảnh
        <textarea
          rows="3"
          placeholder="ví dụ: Kinh nghiệm liên quan, bối cảnh làm việc."
          class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
        ></textarea>
      </label>
      <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
        Tính cách
        <textarea
          rows="3"
          placeholder="ví dụ: Tập trung, nhiệt tình, cần hướng dẫn."
          class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
        ></textarea>
      </label>
      <div class="mt-4 grid gap-4 md:grid-cols-2">
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Mục tiêu
          <textarea
            rows="3"
            placeholder="ví dụ: Hỗ trợ nhóm chính, đảm bảo quy trình chuẩn."
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          ></textarea>
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Speech pattern
          <textarea
            rows="3"
            placeholder="ví dụ: Ngắn gọn, nhiều câu hỏi xác nhận."
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          ></textarea>
        </label>
      </div>
      <div class="mt-4 grid gap-4 md:grid-cols-3">
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Emotion ban đầu
          <input
            type="text"
            placeholder="ví dụ: Lo lắng"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Emotion kết thúc
          <input
            type="text"
            placeholder="ví dụ: An tâm"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
        <label class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Voice tags
          <input
            type="text"
            placeholder="ví dụ: supporter, curious"
            class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
          />
        </label>
      </div>
      <label class="mt-4 block text-xs font-semibold uppercase tracking-wide text-slate-500">
        Emotion trong quá trình
        <textarea
          rows="3"
          placeholder="ví dụ: căng thẳng&#10;hợp tác&#10;nhẹ nhõm"
          class="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-primary-200 focus:outline-none focus:ring-2 focus:ring-primary-100"
        ></textarea>
      </label>
    </div>
  </template>

  <script>
    document.addEventListener("DOMContentLoaded", () => {
      decorateFieldInputs(document);
      document.querySelectorAll("template").forEach((template) => {
        if (template.content) {
          decorateFieldInputs(template.content);
        }
      });

      const tabButtons = document.querySelectorAll("[data-tab]");
      const panels = document.querySelectorAll("[data-panel]");
      const ACTIVE_BUTTON_CLASSES = [
        "bg-primary-600",
        "text-white",
        "border-primary-600",
        "hover:bg-primary-500",
        "hover:text-white",
        "hover:border-primary-600",
        "shadow-md"
      ];
      const INACTIVE_BUTTON_CLASSES = [
        "bg-white",
        "text-primary-600",
        "hover:text-primary-700",
        "hover:border-primary-300"
      ];

      const activateTab = (tabId) => {
        tabButtons.forEach((button) => {
          const isActive = button.dataset.tab === tabId;
          if (isActive) {
            button.classList.add(...ACTIVE_BUTTON_CLASSES);
            button.classList.remove(...INACTIVE_BUTTON_CLASSES);
            button.setAttribute("aria-selected", "true");
            button.setAttribute("tabindex", "0");
          } else {
            button.classList.remove(...ACTIVE_BUTTON_CLASSES);
            button.classList.add(...INACTIVE_BUTTON_CLASSES);
            button.setAttribute("aria-selected", "false");
            button.setAttribute("tabindex", "-1");
          }
        });

        panels.forEach((panel) => {
          if (panel.dataset.panel === tabId) {
            panel.classList.remove("hidden");
          } else {
            panel.classList.add("hidden");
          }
        });
      };

      tabButtons.forEach((button) => {
        button.addEventListener("click", () => activateTab(button.dataset.tab));
      });

      activateTab("skeleton");

      const API_ENDPOINT = "/api/cases";
      const saveCaseButton = document.getElementById("save-case-button");

      const ensureToastRoot = () => {
        let root = document.getElementById("toast-root");
        if (!root) {
          root = document.createElement("div");
          root.id = "toast-root";
          root.className = "fixed top-4 right-4 z-50 flex flex-col gap-3";
          document.body.appendChild(root);
        }
        return root;
      };

      const showNotification = (message, type = "success") => {
        const root = ensureToastRoot();
        const toast = document.createElement("div");
        const baseClasses = "rounded-xl px-4 py-3 text-sm font-semibold shadow-lg backdrop-blur";
        const palette =
          type === "error"
            ? "bg-red-600/90 text-white"
            : type === "info"
            ? "bg-slate-800/90 text-white"
            : "bg-emerald-600/90 text-white";
        toast.className = `${baseClasses} ${palette}`;
        toast.textContent = message;
        root.appendChild(toast);
        setTimeout(() => {
          toast.classList.add("opacity-0", "transition");
          setTimeout(() => {
            toast.remove();
            if (!root.children.length) {
              root.remove();
            }
          }, 200);
        }, 4000);
      };

      const slugify = (value, fallback) => {
        if (!value) {
          return fallback;
        }
        return value
          .toLowerCase()
          .normalize("NFD")
          .replace(/[\u0300-\u036f]/g, "")
          .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_|_$/g, "") || fallback;
  };

  const parseLines = (raw) => {
        if (!raw) return [];
        return raw
          .split(/\r?\n/)
          .map((item) => item.trim())
          .filter(Boolean);
      };

      const parseNPC = (raw) => {
        if (!raw) return [];
        return raw
          .split(/[\n,]+/)
          .map((segment) => {
            const [personaId, ...roleParts] = segment.split(":");
            const id = (personaId || "").trim();
            const role = roleParts.join(":").trim();
            if (!id) return null;
            return role ? { persona_id: id, role } : { persona_id: id };
          })
          .filter(Boolean);
  };

  const normalizeLabelKey = (value) => {
    return (value || "")
      .toString()
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "");
  };

  const RAW_LABEL_SYNONYMS = [
  ["ten case", "ten case"],
  ["ma su kien", "ma su kien"],
  ["tieu de", "tieu de"],
  ["mo ta chi tiet", "mo ta chi tiet"],
  ["chu de case", "chu de case"],
  ["thoi gian", "thoi gian"],
  ["thoi tiet", "thoi tiet"],
  ["vi tri", "vi tri"],
  ["m??cc ???T ??\\", "muc do on ghi chu"],
  ["tom tat su kien", "tom tat su kien"],
  ["tinh trang hien tai", "tinh trang hien tai"],
  ["ai tiep can dau tien", "ai tiep can dau tien"],
  ["ten nhom", "ten nhom"],
  ["ghi chu", "ghi chu"],
  ["danh sA?ch ngu??\\", "danh sach nguon luc"],
  ["rang buoc hien truong", "rang buoc hien truong"],
  ["chinh sach an toan", "chinh sach an toan"],
  ["don vi ban giao", "don vi ban giao"],
  ["trang thai thanh cong cuoi cung", "trang thai thanh cong cuoi cung"],
  ["ten nhan vat", "ten nhan vat"],
  ["vai tro", "vai tro"],
  ["tuoi", "tuoi"],
  ["gioi tinh", "gioi tinh"],
  ["ly lich hoan canh", "ly lich hoan canh"],
  ["tinh cach", "tinh cach"],
  ["muc tieu", "muc tieu"],
  ["emotion ban dau", "emotion ban dau"],
  ["emotion ket thuc", "emotion ket thuc"],
  ["emotion trong qua trinh", "emotion trong qua trinh"],
];

const FIELD_LABEL_SYNONYMS = RAW_LABEL_SYNONYMS.reduce((acc, pair) => {
  const [a, b] = pair;
  if (!acc[a]) acc[a] = [];
  if (!acc[a].includes(b)) acc[a].push(b);
  if (!acc[b]) acc[b] = [];
  if (!acc[b].includes(a)) acc[b].push(a);
  return acc;
}, {});
FIELD_LABEL_SYNONYMS.npc = ['npc xuat hien'];
FIELD_LABEL_SYNONYMS['npc xuat hien'] = ['npc'];


  const resolveFieldKey = (value) => {
    const raw = (value || "").trim().toLowerCase();
    for (const [original, canonical] of RAW_LABEL_SYNONYMS) {
      if (original.toLowerCase() === raw) {
        return canonical;
      }
      if (canonical.toLowerCase() === raw) {
        return canonical;
      }
    }
    return value || "";
  };

  const expandKeywordVariants = (keyword) => {
    const queue = Array.isArray(keyword) ? [...keyword] : [keyword];
    const result = [];
    const seen = new Set();
    while (queue.length) {
      const current = queue.shift();
      if (!current || seen.has(current)) {
        continue;
      }
      seen.add(current);
      result.push(current);
      const extras = FIELD_LABEL_SYNONYMS[current];
      if (Array.isArray(extras)) {
        extras.forEach((item) => {
          if (!seen.has(item)) {
            queue.push(item);
          }
        });
      }
    }
    return result;
  };

  const decorateFieldInputs = (root) => {
    if (!root) {
      return;
    }
    const labels = root.querySelectorAll("label");
    labels.forEach((label) => {
      const field = label.querySelector("input, textarea");
      if (!field) {
        return;
      }
      const resolvedKey = resolveFieldKey(label.textContent || "");
      const normalizedKey = normalizeLabelKey(resolvedKey);
      if (normalizedKey) {
        field.dataset.fieldKey = normalizedKey;
      }
      if (resolvedKey) {
        field.dataset.fieldKeyRaw = resolvedKey.toLowerCase();
      }
    });
  };

      const findFieldByLabel = (root, keyword) => {
        if (!root) return null;
        const variants = expandKeywordVariants(keyword);
        const targetKeys = variants
          .map((item) => normalizeLabelKey(resolveFieldKey(item)))
          .filter(Boolean);
        const rawKeys = variants
          .map((item) => resolveFieldKey(item).toLowerCase())
          .filter(Boolean);

        if (!targetKeys.length) {
          return null;
        }

        const matchesKey = (value) => {
          if (!value) {
            return false;
          }
          const normalized = normalizeLabelKey(resolveFieldKey(value));
          if (!normalized) {
            return false;
          }
          return targetKeys.some(
            (key) => normalized.includes(key) || key.includes(normalized)
          );
        };

        const labels = Array.from(root.querySelectorAll("label"));
        for (const label of labels) {
          if (matchesKey(label.textContent || "")) {
            return label.querySelector("input, textarea");
          }
        }

        const fields = Array.from(root.querySelectorAll("input, textarea"));
        for (const field of fields) {
          const candidates = [
            field.dataset.fieldKey,
            field.dataset.fieldKeyRaw,
            field.name,
            field.id,
            field.getAttribute("aria-label"),
            field.getAttribute("placeholder"),
          ];
          for (const candidate of candidates) {
            if (matchesKey(candidate)) {
              const datasetKey = field.dataset.fieldKey;
              if (!datasetKey) {
                const preferred = targetKeys[0];
                if (preferred) {
                  field.dataset.fieldKey = preferred;
                }
              }
              const datasetRaw = field.dataset.fieldKeyRaw;
              if (!datasetRaw && rawKeys[0]) {
                field.dataset.fieldKeyRaw = rawKeys[0];
              }
              return field;
            }
          }
        }
        return null;
      };

      const assignFieldValue = (root, keyword, rawValue) => {
        if (!root) {
          return;
        }
        const variants = expandKeywordVariants(keyword);
        for (const variant of variants) {
          const field = findFieldByLabel(root, variant);
          if (!field) {
            continue;
          }
          const value =
            rawValue === null || rawValue === undefined
              ? ""
              : Array.isArray(rawValue)
              ? rawValue.join("\n")
              : String(rawValue);
          field.value = value;
          field.dispatchEvent(new Event("input", { bubbles: true }));
          return;
        }
      };

      const extractSkeleton = () => {
        const skeletonPanel = document.querySelector('[data-panel="skeleton"]');
        if (!skeletonPanel) {
          return { case_id: "", title: "", canon_events: [] };
        }
        const form = skeletonPanel.querySelector("form");
        const caseId = (findFieldByLabel(form, "case id")?.value || "").trim();
        const caseTitle = (findFieldByLabel(form, "tên case")?.value || "").trim();

        const events = Array.from(form.querySelectorAll("[data-event-block]"))
          .map((block, index) => {
            const eventId = (findFieldByLabel(block, "mã sự kiện")?.value || "").trim();
            const title = (findFieldByLabel(block, "tiêu đề")?.value || "").trim();
            const description = (findFieldByLabel(block, "mô tả chi tiết")?.value || "").trim();
            const successRaw = findFieldByLabel(block, "success criteria")?.value || "";
            const npcRaw = (findFieldByLabel(block, "npc xuat hien")?.value || "").trim();
            const timeoutRaw = (findFieldByLabel(block, "timeout")?.value || "").trim();
            const onSuccess = (findFieldByLabel(block, "on success")?.value || "").trim();
            const onFail = (findFieldByLabel(block, "on fail")?.value || "").trim();

            const hasContent =
              eventId ||
              title ||
              description ||
              successRaw.trim() ||
              npcRaw ||
              timeoutRaw ||
              onSuccess ||
              onFail;
            if (!hasContent) {
              return null;
            }

            const timeout = timeoutRaw ? Number.parseInt(timeoutRaw, 10) : null;

            return {
              id: eventId || `event_${index + 1}`,
              title,
              description,
              success_criteria: parseLines(successRaw),
              npc_appearance: parseNPC(npcRaw),
              timeout_turn: Number.isFinite(timeout) ? timeout : null,
              preconditions: [],
              on_success: onSuccess || null,
              on_fail: onFail || null,
            };
          })
          .filter(Boolean);

        return {
          case_id: caseId,
          title: caseTitle,
          canon_events: events,
        };
      };

      const extractContext = () => {
        const contextPanel = document.querySelector('[data-panel="context"]');
        if (!contextPanel) {
          return {
            case_id: "",
            topic: "",
            initial_context: {
              scene: { time: "", weather: "", location: "", noise_level: "" },
              index_event: { summary: "", current_state: "", who_first_on_scene: "" },
              available_resources: {},
              constraints: [],
              policies_safety_legal: [],
              handover_target: "",
              success_end_state: "",
            },
          };
        }

        const form = contextPanel.querySelector("form");
        const caseId = (findFieldByLabel(form, "case id")?.value || "").trim();
        const topic = (findFieldByLabel(form, "chủ đề case")?.value || "").trim();

        const scene = {
          time: (findFieldByLabel(form, "thời gian")?.value || "").trim(),
          weather: (findFieldByLabel(form, "thời tiết")?.value || "").trim(),
          location: (findFieldByLabel(form, "vị trí")?.value || "").trim(),
          noise_level: (findFieldByLabel(form, "mức độ ồn")?.value || "").trim(),
        };

        const indexEvent = {
          summary: (findFieldByLabel(form, "tóm tắt sự kiện")?.value || "").trim(),
          current_state: (findFieldByLabel(form, "tình trạng hiện tại")?.value || "").trim(),
          who_first_on_scene: (findFieldByLabel(form, "ai tiếp cận đầu tiên")?.value || "").trim(),
        };

        const resourceBlocks = Array.from(form.querySelectorAll("[data-resource-block]"));
        const availableResources = {};
        const resourceMeta = {};

        resourceBlocks.forEach((block, index) => {
          const name = (findFieldByLabel(block, "tên nhóm")?.value || "").trim();
          const note = (findFieldByLabel(block, "ghi chú")?.value || "").trim();
          const items = parseLines(findFieldByLabel(block, "danh sách nguồn lực")?.value || "");
          if (!name && !note && !items.length) {
            return;
          }
          const key = slugify(name, `resource_${index + 1}`);
          const resources = [...items];
          if (note) {
            resources.push(`NOTE: ${note}`);
          }
          availableResources[key] = resources;
          resourceMeta[key] = {
            label: name || `Nhóm ${index + 1}`,
            note: note || "",
          };
        });

        const constraints = parseLines(findFieldByLabel(form, "ràng buộc hiện trường")?.value || "");
        const policies = parseLines(findFieldByLabel(form, "chính sách")?.value || "");
        const handoverTarget = (findFieldByLabel(form, "đơn vị bàn giao")?.value || "").trim();
        const successEndState = (findFieldByLabel(form, "trạng thái thành công cuối cùng")?.value || "").trim();

        const initialContext = {
          scene,
          index_event: indexEvent,
          available_resources: availableResources,
          constraints,
          policies_safety_legal: policies,
          handover_target: handoverTarget,
          success_end_state: successEndState,
        };

        if (Object.keys(resourceMeta).length) {
          initialContext.available_resources_meta = resourceMeta;
        }

        return {
          case_id: caseId,
          topic,
          initial_context: initialContext,
        };
      };

      const extractPersonas = () => {
        const personasPanel = document.querySelector('[data-panel="personas"]');
        if (!personasPanel) {
          return { case_id: "", personas: [] };
        }

        const form = personasPanel.querySelector("form");
        const caseId = (findFieldByLabel(form, "case id")?.value || "").trim();

        const personas = Array.from(form.querySelectorAll("[data-persona-item]"))
          .map((item, index) => {
            const id = (findFieldByLabel(item, "persona id")?.value || "").trim();
            const name = (findFieldByLabel(item, "tên nhân vật")?.value || "").trim();
            const role = (findFieldByLabel(item, "vai trò")?.value || "").trim();
            const ageRaw = (findFieldByLabel(item, "tuổi")?.value || "").trim();
            const gender = (findFieldByLabel(item, "giới tính")?.value || "").trim();
            const background = (findFieldByLabel(item, "lý lịch")?.value || "").trim();
            const personality = (findFieldByLabel(item, "tính cách")?.value || "").trim();
            const goal = (findFieldByLabel(item, "mục tiêu")?.value || "").trim();
            const speechPattern = (findFieldByLabel(item, "speech pattern")?.value || "").trim();
            const emotionInit = (findFieldByLabel(item, "emotion ban đầu")?.value || "").trim();
            const emotionEnd = (findFieldByLabel(item, "emotion kết thúc")?.value || "").trim();
            const voiceTagsRaw = (findFieldByLabel(item, "voice tags")?.value || "").trim();
            const emotionDuring = parseLines(
              findFieldByLabel(item, "emotion trong quá trình")?.value || ""
            );

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
              voiceTagsRaw ||
              emotionDuring.length;
            if (!hasContent) {
              return null;
            }

            const age = ageRaw ? Number.parseInt(ageRaw, 10) : null;
            const voiceTags = voiceTagsRaw
              ? voiceTagsRaw
                  .split(/[;,]/)
                  .map((tag) => tag.trim())
                  .filter(Boolean)
              : [];

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
          })
          .filter(Boolean);

        return {
          case_id: caseId,
          personas,
        };
      };

      const buildCasePayload = () => {
        const skeleton = extractSkeleton();
        const context = extractContext();
        const personasPayload = extractPersonas();

        const resolvedCaseId =
          skeleton.case_id || context.case_id || personasPayload.case_id;

        if (!resolvedCaseId) {
          throw new Error("Vui lòng nhập Case ID ở ít nhất một tab trước khi lưu.");
        }

        skeleton.case_id = skeleton.case_id || resolvedCaseId;
        context.case_id = context.case_id || resolvedCaseId;
        personasPayload.case_id = personasPayload.case_id || resolvedCaseId;

        return {
          case_id: resolvedCaseId,
          context,
          personas: {
            case_id: personasPayload.case_id,
            personas: personasPayload.personas,
          },
          skeleton,
        };
      };

      const getValidationState = () => {
        const skeleton = extractSkeleton();
        const context = extractContext();
        const personasPayload = extractPersonas();

        const issues = {
          global: [],
          skeleton: [],
          context: [],
          personas: [],
        };

        const resolvedCaseId =
          skeleton.case_id || context.case_id || personasPayload.case_id;

        if (!resolvedCaseId) {
          issues.global.push("Case ID");
        }

        if (!skeleton.title) {
          issues.skeleton.push("Tên case");
        }
        if (!skeleton.canon_events.length) {
          issues.skeleton.push("Ít nhất 1 Canon Event");
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
          issues.context.push("Chủ đề case");
        }
        if (!scene.time) {
          issues.context.push("Thời gian trong Scene");
        }
        if (!scene.location) {
          issues.context.push("Địa điểm trong Scene");
        }
        if (!indexEvent.summary) {
          issues.context.push("Tóm tắt sự kiện ban đầu");
        }
        if (!indexEvent.who_first_on_scene) {
          issues.context.push("Ai tiếp cận đầu tiên");
        }

        if (!personasPayload.personas.length) {
          issues.personas.push("Ít nhất 1 persona");
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
          skeleton,
          context,
          personasPayload,
          issues,
          isComplete,
        };
      };

      const updateSaveButtonState = () => {
        if (!saveCaseButton) {
          return;
        }
        const { isComplete } = getValidationState();
        saveCaseButton.disabled = !isComplete;
        saveCaseButton.classList.toggle("cursor-not-allowed", !isComplete);
        saveCaseButton.classList.toggle("bg-white", !isComplete);
        saveCaseButton.classList.toggle("text-slate-400", !isComplete);
        saveCaseButton.classList.toggle("border-slate-200", !isComplete);
        saveCaseButton.classList.toggle("bg-primary-600", isComplete);
        saveCaseButton.classList.toggle("text-white", isComplete);
        saveCaseButton.classList.toggle("border-transparent", isComplete);
        saveCaseButton.classList.toggle("hover:bg-primary-500", isComplete);
      };

      const formatMissingMessages = (issues) => {
        const parts = [];
        if (issues.global.length) {
          parts.push(`Chung: ${issues.global.join(", ")}`);
        }
        if (issues.skeleton.length) {
          parts.push(`Skeleton: ${issues.skeleton.join(", ")}`);
        }
        if (issues.context.length) {
          parts.push(`Context: ${issues.context.join(", ")}`);
        }
        if (issues.personas.length) {
          parts.push(`Personas: ${issues.personas.join(", ")}`);
        }
        return parts.join(" | ");
      };

      const resetAllForms = () => {
        document.querySelectorAll("form[data-prevent-submit]").forEach((form) => {
          form.reset();
        });

        const cleanupContainer = (selector, itemSelector) => {
          const container = document.querySelector(selector);
          if (!container) return;
          const items = Array.from(container.querySelectorAll(itemSelector));
          items.forEach((item, index) => {
            if (index === 0) {
              item.querySelectorAll("input, textarea").forEach((field) => {
                field.value = "";
              });
            } else {
              item.remove();
            }
          });
        };

        cleanupContainer("[data-resource-list]", "[data-resource-block]");
        cleanupContainer("[data-skeleton-events]", "[data-event-block]");
        cleanupContainer("[data-persona-list]", "[data-persona-item]");
        decorateFieldInputs(document);
      };

      const toggleButtonState = (button, isLoading) => {
        if (!button) return;
        if (isLoading) {
          button.dataset.originalText = button.textContent || "";
          button.disabled = true;
          button.textContent = "Đang lưu...";
          button.classList.add("opacity-60", "cursor-wait");
        } else {
          button.disabled = false;
          if (button.dataset.originalText) {
            button.textContent = button.dataset.originalText;
            delete button.dataset.originalText;
          }
          button.classList.remove("opacity-60", "cursor-wait");
        }
      };

      const handleCaseSave = async () => {
        if (!saveCaseButton) {
          return;
        }

        const validation = getValidationState();
        if (!validation.isComplete) {
          const message = formatMissingMessages(validation.issues);
          showNotification(
            message
              ? `Vui lòng bổ sung thông tin trước khi lưu: ${message}`
              : "Vui lòng hoàn thiện cả 3 biểu mẫu trước khi lưu.",
            "error"
          );
          return;
        }

        toggleButtonState(saveCaseButton, true);

        try {
          const payload = buildCasePayload();
          if (!payload.skeleton.canon_events.length) {
            throw new Error("Vui lòng nhập ít nhất một Canon Event.");
          }
          if (!payload.personas.personas.length) {
            throw new Error("Vui lòng nhập ít nhất một Persona.");
          }

          showNotification("Đang gửi dữ liệu lên máy chủ...", "info");
          const response = await fetch(API_ENDPOINT, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            credentials: "same-origin",
            body: JSON.stringify(payload),
          });

          const contentType = response.headers.get("content-type") || "";
          const responseData = contentType.includes("application/json") ? await response.json() : null;

          if (!response.ok) {
            const detail =
              (responseData && (responseData.detail || responseData.message)) ||
              "Không thể lưu case. Vui lòng thử lại.";
            throw new Error(detail);
          }

          const payloadInfo = {
            case_id: responseData?.case_id ?? payload.case_id,
            personas_count:
              typeof responseData?.personas_count === "number"
                ? responseData.personas_count
                : payload.personas.personas.length,
          };

          showNotification(
            `Đã lưu case '${payloadInfo.case_id}' thành công (${payloadInfo.personas_count} personas).`
          );
          resetAllForms();
          if (typeof clearSectionImport === "function") {
            clearSectionImport("skeleton", { silent: true });
            clearSectionImport("context", { silent: true });
            clearSectionImport("personas", { silent: true });
          }
        } catch (error) {
          console.error(error);
          showNotification(error.message || "Có lỗi xảy ra khi lưu case.", "error");
        } finally {
          toggleButtonState(saveCaseButton, false);
          updateSaveButtonState();
        }
      };

      document.addEventListener("input", () => {
        updateSaveButtonState();
      });

      document.querySelectorAll("form[data-prevent-submit]").forEach((form) => {
        form.addEventListener("submit", (event) => {
          event.preventDefault();
          handleCaseSave();
        });
        form.addEventListener("reset", () => {
          setTimeout(() => {
            updateSaveButtonState();
          }, 0);
        });
      });

      if (saveCaseButton) {
        saveCaseButton.addEventListener("click", handleCaseSave);
      }

      document.querySelectorAll("[data-next-tab]").forEach((button) => {
        button.addEventListener("click", () => {
          const target = button.dataset.nextTab;
          if (target) {
            activateTab(target);
          }
        });
      });

      document.querySelectorAll("[data-prev-tab]").forEach((button) => {
        button.addEventListener("click", () => {
          const target = button.dataset.prevTab;
          if (target) {
            activateTab(target);
          }
        });
      });

      updateSaveButtonState();

      const resourceList = document.querySelector("[data-resource-list]");
      const resourceTemplate = document.getElementById("resource-template");

      const initResourceBlock = (block) => {
        decorateFieldInputs(block);
        const removeBtn = block.querySelector("[data-remove-resource]");
        if (!removeBtn) {
          return;
        }

        removeBtn.addEventListener("click", () => {
          if (!resourceList) return;
          if (resourceList.children.length === 1) {
            block.querySelectorAll("input, textarea").forEach((field) => {
              field.value = "";
            });
            updateSaveButtonState();
            return;
          }
          block.remove();
          updateSaveButtonState();
        });
      };

      if (resourceList) {
        resourceList.querySelectorAll("[data-resource-block]").forEach(initResourceBlock);
      }

      const addResourceBtn = document.querySelector("[data-add-resource]");
      if (addResourceBtn && resourceTemplate && resourceList) {
        addResourceBtn.addEventListener("click", () => {
          const clone = resourceTemplate.content.firstElementChild.cloneNode(true);
          resourceList.appendChild(clone);
          initResourceBlock(clone);
          updateSaveButtonState();
        });
      }

      const skeletonEventsContainer = document.querySelector("[data-skeleton-events]");
      const eventTemplate = document.getElementById("skeleton-event-template");

      const initEventBlock = (block) => {
        decorateFieldInputs(block);
        const removeBtn = block.querySelector("[data-remove-event]");
        if (removeBtn) {
          removeBtn.addEventListener("click", () => {
            if (!skeletonEventsContainer) return;
            if (skeletonEventsContainer.children.length === 1) {
              block.querySelectorAll("input, textarea").forEach((field) => {
                field.value = "";
              });
              updateSaveButtonState();
              return;
            }
            block.remove();
            updateSaveButtonState();
          });
        }
      };

      if (skeletonEventsContainer) {
        skeletonEventsContainer.querySelectorAll("[data-event-block]").forEach(initEventBlock);
      }

      const addEventBtn = document.querySelector("[data-add-event]");
      if (addEventBtn && eventTemplate && skeletonEventsContainer) {
        addEventBtn.addEventListener("click", () => {
          const clone = eventTemplate.content.firstElementChild.cloneNode(true);
          skeletonEventsContainer.appendChild(clone);
          initEventBlock(clone);
          updateSaveButtonState();
        });
      }

      const personaList = document.querySelector("[data-persona-list]");
      const personaTemplate = document.getElementById("persona-template");

      const initPersonaItem = (item) => {
        decorateFieldInputs(item);
        const removeBtn = item.querySelector("[data-remove-persona]");
        if (removeBtn) {
          removeBtn.addEventListener("click", () => {
            if (!personaList) return;
            if (personaList.children.length === 1) {
              item.querySelectorAll("input, textarea").forEach((field) => {
                field.value = "";
              });
              updateSaveButtonState();
              return;
            }
            item.remove();
            updateSaveButtonState();
          });
        }
      };

      if (personaList) {
        personaList.querySelectorAll("[data-persona-item]").forEach(initPersonaItem);
      }

      const addPersonaBtn = document.querySelector("[data-add-persona]");
      if (addPersonaBtn && personaTemplate && personaList) {
        addPersonaBtn.addEventListener("click", () => {
          const clone = personaTemplate.content.firstElementChild.cloneNode(true);
          personaList.appendChild(clone);
          initPersonaItem(clone);
          updateSaveButtonState();
        });
      }

      const ensureListSize = (container, template, desiredCount, initCallback) => {
        if (!container || !template) {
          return [];
        }
        const targetCount = Math.max(desiredCount, 1);
        while (container.children.length > targetCount) {
          container.removeChild(container.lastElementChild);
        }
        while (container.children.length < targetCount) {
          const clone = template.content.firstElementChild.cloneNode(true);
          container.appendChild(clone);
          decorateFieldInputs(clone);
          if (typeof initCallback === "function") {
            initCallback(clone);
          }
        }
        decorateFieldInputs(container);
        return Array.from(container.children);
      };

      const clearInputs = (root) => {
        if (!root) return;
        root.querySelectorAll("input, textarea").forEach((field) => {
          field.value = "";
          field.dispatchEvent(new Event("input", { bubbles: true }));
        });
      };

      const formatLines = (value) => {
        if (Array.isArray(value)) {
          return value
            .map((item) => (typeof item === "string" ? item.trim() : ""))
            .filter(Boolean)
            .join("\n");
        }
        return typeof value === "string" ? value : "";
      };

      const formatVoiceTags = (tags) => {
        if (Array.isArray(tags)) {
          return tags
            .map((tag) => (typeof tag === "string" ? tag.trim() : ""))
            .filter(Boolean)
            .join(", ");
        }
        return typeof tags === "string" ? tags : "";
      };

      const formatNpcAppearance = (list) => {
        if (Array.isArray(list)) {
          return list
            .map((entry) => {
              if (!entry) {
                return "";
              }
              if (typeof entry === "string") {
                return entry.trim();
              }
              const id = (entry.persona_id || entry.id || "").trim();
              const role = (entry.role || entry.title || "").trim();
              if (id && role) {
                return `${id}: ${role}`;
              }
              return id || role;
            })
            .filter(Boolean)
            .join("\n");
        }
        return typeof list === "string" ? list : "";
      };

      const populateCaseForms = (payload, options = {}) => {
        if (!payload || typeof payload !== "object") {
          throw new Error("Tap tin JSON khong dung dinh dang.");
        }

        const skeletonData =
          payload.skeleton && typeof payload.skeleton === "object" ? payload.skeleton : {};
        const contextData =
          payload.context && typeof payload.context === "object" ? payload.context : {};
        const personasData =
          payload.personas && typeof payload.personas === "object" ? payload.personas : {};

        const resolvedCaseId =
          payload.case_id ||
          skeletonData.case_id ||
          contextData.case_id ||
          personasData.case_id ||
          "";

        const {
          reset = true,
          sections,
          activeTab = "skeleton",
        } = options;

        const targetSections =
          Array.isArray(sections) && sections.length
            ? new Set(sections)
            : new Set(["skeleton", "context", "personas"]);

        if (reset) {
          resetAllForms();
        }

        const skeletonPanel = document.querySelector('[data-panel="skeleton"]');
        const contextPanel = document.querySelector('[data-panel="context"]');
        const personasPanel = document.querySelector('[data-panel="personas"]');

        const skeletonForm = skeletonPanel ? skeletonPanel.querySelector("form") : null;
        const contextForm = contextPanel ? contextPanel.querySelector("form") : null;
        const personasForm = personasPanel ? personasPanel.querySelector("form") : null;

        if (targetSections.has("skeleton") && skeletonForm) {
          assignFieldValue(skeletonForm, "case id", skeletonData.case_id || resolvedCaseId);
          assignFieldValue(skeletonForm, "tA�n case", skeletonData.title || "");

          const events = Array.isArray(skeletonData.canon_events) ? skeletonData.canon_events : [];
          const eventBlocks = ensureListSize(
            skeletonEventsContainer,
            eventTemplate,
            events.length || 1,
            initEventBlock
          );
          eventBlocks.forEach((block, index) => {
            const eventData = events[index];
            if (!eventData) {
              clearInputs(block);
              return;
            }
            assignFieldValue(block, "mA� s��� ki���n", eventData.id || "");
            assignFieldValue(block, "tiA�u �`��?", eventData.title || "");
            assignFieldValue(block, "mA' t��� chi ti���t", eventData.description || "");
            assignFieldValue(block, "success criteria", formatLines(eventData.success_criteria));
            assignFieldValue(block, "npc xuat hien", formatNpcAppearance(eventData.npc_appearance));
            assignFieldValue(block, "timeout", eventData.timeout_turn ?? "");
            assignFieldValue(block, "on success", eventData.on_success || "");
            assignFieldValue(block, "on fail", eventData.on_fail || "");
          });
        }

        if (targetSections.has("context") && contextForm) {
          assignFieldValue(contextForm, "case id", contextData.case_id || resolvedCaseId);
          assignFieldValue(contextForm, "ch�� �`��? case", contextData.topic || "");

          const initialContext =
            contextData.initial_context && typeof contextData.initial_context === "object"
              ? contextData.initial_context
              : {};
          const scene =
            initialContext.scene && typeof initialContext.scene === "object"
              ? initialContext.scene
              : {};
          assignFieldValue(contextForm, "th��?i gian", scene.time || "");
          assignFieldValue(contextForm, "th��?i ti���t", scene.weather || "");
          assignFieldValue(contextForm, "v��< trA-", scene.location || "");
          assignFieldValue(contextForm, "m��cc �`��T ��\"n", scene.noise_level || "");

          const indexEvent =
            initialContext.index_event && typeof initialContext.index_event === "object"
              ? initialContext.index_event
              : {};
          assignFieldValue(contextForm, "tA3m t��_t s��� ki���n", indexEvent.summary || "");
          assignFieldValue(contextForm, "tA�nh tr���ng hi���n t���i", indexEvent.current_state || "");
          assignFieldValue(contextForm, "ai ti���p c��-n �`��u tiA�n", indexEvent.who_first_on_scene || "");

          const availableResources =
            initialContext.available_resources && typeof initialContext.available_resources === "object"
              ? initialContext.available_resources
              : {};
          const availableMeta =
            initialContext.available_resources_meta &&
            typeof initialContext.available_resources_meta === "object"
              ? initialContext.available_resources_meta
              : {};

          const resourceKeys = Object.keys(availableResources);
          const resourceBlocks = ensureListSize(
            resourceList,
            resourceTemplate,
            resourceKeys.length || 1,
            initResourceBlock
          );
          resourceBlocks.forEach((block, index) => {
            const key = resourceKeys[index];
            if (!key) {
              clearInputs(block);
              return;
            }
            const entries = Array.isArray(availableResources[key]) ? availableResources[key] : [];
            const meta = availableMeta[key] || {};
            const items = [];
            let note = meta.note || "";
            entries.forEach((entry) => {
              if (typeof entry !== "string") {
                return;
              }
              const trimmed = entry.trim();
              if (!trimmed) {
                return;
              }
              if (!meta.note && trimmed.toUpperCase().startsWith("NOTE:")) {
                note = trimmed.slice(5).trim();
              } else {
                items.push(trimmed);
              }
            });
            assignFieldValue(block, "tA�n nhA3m", meta.label || key);
            assignFieldValue(block, "ghi chA�", note);
            assignFieldValue(block, "danh sA�ch ngu��\"n l���c", items.join("\n"));
          });

          assignFieldValue(
            contextForm,
            "rA�ng bu��Tc hi���n tr����?ng",
            formatLines(initialContext.constraints)
          );
          assignFieldValue(contextForm, "chA-nh sA�ch", formatLines(initialContext.policies_safety_legal));
          assignFieldValue(contextForm, "�`��n v��< bA�n giao", initialContext.handover_target || "");
          assignFieldValue(
            contextForm,
            "tr���ng thA�i thA�nh cA'ng cu��`i cA1ng",
            initialContext.success_end_state || ""
          );
        }

        if (targetSections.has("personas") && personasForm) {
          assignFieldValue(personasForm, "case id", personasData.case_id || resolvedCaseId);
          const personas = Array.isArray(personasData.personas) ? personasData.personas : [];
          const personaCountField = findFieldByLabel(personasForm, "so luong persona");
          if (personaCountField) {
            personaCountField.value = personas.length ? String(personas.length) : "";
            personaCountField.dispatchEvent(new Event("input", { bubbles: true }));
          }
          const personaBlocks = ensureListSize(
            personaList,
            personaTemplate,
            personas.length || 1,
            initPersonaItem
          );
          personaBlocks.forEach((item, index) => {
            const persona = personas[index];
            if (!persona) {
              clearInputs(item);
              return;
            }
            assignFieldValue(item, "persona id", persona.id || "");
            assignFieldValue(item, "tA�n nhA�n v��-t", persona.name || "");
            assignFieldValue(item, "vai trA�", persona.role || "");
            assignFieldValue(item, "tu��i", persona.age ?? "");
            assignFieldValue(item, "gi��>i tA-nh", persona.gender || "");
            assignFieldValue(item, "lA� l��<ch", persona.background || "");
            assignFieldValue(item, "tA-nh cA�ch", persona.personality || "");
            assignFieldValue(item, "m���c tiA�u", persona.goal || "");
            assignFieldValue(item, "speech pattern", persona.speech_pattern || "");
            assignFieldValue(item, "emotion ban �`��u", persona.emotion_init || "");
            assignFieldValue(item, "emotion k���t thA�c", persona.emotion_end || "");
            assignFieldValue(item, "voice tags", formatVoiceTags(persona.voice_tags));
            assignFieldValue(item, "emotion trong quA� trA�nh", formatLines(persona.emotion_during));
          });
        }

        if (activeTab) {
          activateTab(activeTab);
        }
        updateSaveButtonState();
        return resolvedCaseId;
      };



      const JSON_SECTION_TYPES = ['skeleton', 'context', 'personas'];
      const JSON_SECTION_LABELS = {
        skeleton: 'Skeleton',
        context: 'Context',
        personas: 'Personas',
      };

      const importState = {
        skeleton: null,
        context: null,
        personas: null,
      };

      const hasAnyImportedSection = () =>
        JSON_SECTION_TYPES.some((type) => Boolean(importState[type]?.data));

      const getAggregatedCaseId = () =>
        importState.skeleton?.caseId ||
        importState.context?.caseId ||
        importState.personas?.caseId ||
        '';

      const updateImportStatus = (type) => {
        const statusEl = document.querySelector('[data-json-status="' + type + '"]');
        const zone = document.querySelector('[data-json-section="' + type + '"]');
        if (!statusEl || !zone) {
          return;
        }
        const entry = importState[type];
        const hasEntry = Boolean(entry);

        statusEl.classList.toggle('text-slate-500', !hasEntry);
        statusEl.classList.toggle('text-primary-700', hasEntry);
        statusEl.classList.toggle('font-semibold', hasEntry);
        zone.classList.toggle('border-primary-400', hasEntry);
        zone.classList.toggle('bg-primary-50', hasEntry);
        zone.classList.toggle('shadow', hasEntry);

        if (hasEntry) {
          const parts = ['Da chon ' + entry.fileName];
          if (entry.caseId) {
            parts.push('Case ' + entry.caseId);
          }
          if (type === 'personas') {
            const personasList = Array.isArray(entry.data?.personas) ? entry.data.personas : [];
            if (personasList.length) {
              parts.push(personasList.length + ' personas');
            }
          }
          statusEl.textContent = parts.join(' - ');
        } else {
          statusEl.textContent = 'Chua chon file';
        }
      };

      const refreshAllImportStatuses = () => {
        JSON_SECTION_TYPES.forEach((item) => updateImportStatus(item));
      };

      const normalizeSectionPayload = (type, payload) => {
        if (!payload || typeof payload !== 'object') {
          throw new Error('Tap tin JSON khong dung dinh dang.');
        }

        if (type === 'skeleton') {
          const skeleton =
            payload.skeleton && typeof payload.skeleton === 'object' ? payload.skeleton : payload;
          if (!skeleton || typeof skeleton !== 'object') {
            throw new Error('File Skeleton JSON khong dung dinh dang.');
          }
          return {
            data: skeleton,
            caseId: skeleton.case_id || payload.case_id || '',
          };
        }

        if (type === 'context') {
          const context =
            payload.context && typeof payload.context === 'object' ? payload.context : payload;
          if (!context || typeof context !== 'object') {
            throw new Error('File Context JSON khong dung dinh dang.');
          }
          return {
            data: context,
            caseId: context.case_id || payload.case_id || '',
          };
        }

        if (type === 'personas') {
          let personasContainer = null;
          if (
            payload.personas &&
            typeof payload.personas === 'object' &&
            Array.isArray(payload.personas.personas)
          ) {
            personasContainer = payload.personas;
          } else if (Array.isArray(payload.personas)) {
            personasContainer = { personas: payload.personas };
          } else if (Array.isArray(payload)) {
            personasContainer = { personas: payload };
          } else {
            personasContainer = payload;
          }

          if (
            !personasContainer ||
            typeof personasContainer !== 'object' ||
            !Array.isArray(personasContainer.personas)
          ) {
            throw new Error('File Personas JSON khong dung dinh dang.');
          }
          return {
            data: personasContainer,
            caseId: personasContainer.case_id || payload.case_id || '',
          };
        }

        throw new Error('Loai file JSON khong duoc ho tro.');
      };

      const applySectionImport = (type, parsed, fileName) => {
        try {
          const normalized = normalizeSectionPayload(type, parsed);
          const hadImportBefore = hasAnyImportedSection();
          const fallbackCaseId = normalized.caseId || getAggregatedCaseId();

          importState[type] = {
            data: normalized.data,
            caseId: normalized.caseId || fallbackCaseId || '',
            fileName,
          };

          const payloadForPopulate = {
            case_id: importState[type].caseId,
          };
          payloadForPopulate[type] = normalized.data;

          const sectionsToPopulate = hadImportBefore ? [type] : JSON_SECTION_TYPES;
          const resolvedCaseId = populateCaseForms(payloadForPopulate, {
            reset: !hadImportBefore,
            sections: sectionsToPopulate,
            activeTab: type,
          });

          if (resolvedCaseId) {
            JSON_SECTION_TYPES.forEach((section) => {
              if (importState[section]) {
                importState[section].caseId = resolvedCaseId;
              }
            });
          }

          refreshAllImportStatuses();

          const label = JSON_SECTION_LABELS[type] || type;
          const casePart = resolvedCaseId ? ' (case ' + resolvedCaseId + ')' : '';
          let extra = '';
          if (type === 'personas') {
            const personasList = Array.isArray(normalized.data.personas) ? normalized.data.personas : [];
            if (personasList.length) {
              extra = ' - ' + personasList.length + ' personas';
            }
          }
          showNotification('Da nap ' + label + " tu '" + fileName + "'" + casePart + extra + '.');
        } catch (error) {
          console.error(error);
          showNotification(error.message || 'Khong the nap du lieu tu file JSON.', 'error');
        }
      };

      const clearSectionImport = (type, { silent = false } = {}) => {
        importState[type] = null;

        const currentPanel =
          document.querySelector('[data-panel]:not(.hidden)')?.dataset.panel || 'skeleton';

        populateCaseForms({}, {
          reset: true,
          sections: JSON_SECTION_TYPES,
          activeTab: currentPanel,
        });

        JSON_SECTION_TYPES.forEach((section) => {
          const entry = importState[section];
          if (!entry) {
            return;
          }
          const payload = { case_id: entry.caseId };
          payload[section] = entry.data;
          populateCaseForms(payload, {
            reset: false,
            sections: [section],
            activeTab: null,
          });
        });

        refreshAllImportStatuses();

        if (!silent) {
          const label = JSON_SECTION_LABELS[type] || type;
          showNotification('Da xoa du lieu ' + label + '.', 'info');
        }

        updateSaveButtonState();
      };

      const isJsonFile = (file) => {
        if (!file) {
          return false;
        }
        const name = (file.name || '').toLowerCase();
        const typeName = (file.type || '').toLowerCase();
        return name.endsWith('.json') || typeName.includes('json');
      };

      const readJsonFile = (file) =>
        new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
            try {
              const text = typeof reader.result === 'string' ? reader.result : '';
              resolve(JSON.parse(text));
            } catch (error) {
              reject(new Error('Noi dung file JSON khong hop le.'));
            }
          };
          reader.onerror = () => {
            reject(reader.error || new Error('Khong the doc file JSON.'));
          };
          reader.readAsText(file);
        });

      const processSectionFile = (type, file) => {
        if (!file) {
          return;
        }
        if (!isJsonFile(file)) {
          showNotification('Vui long chon file JSON hop le.', 'error');
          return;
        }
        readJsonFile(file)
          .then((parsed) => {
            applySectionImport(type, parsed, file.name);
          })
          .catch((error) => {
            console.error(error);
            showNotification(error.message || 'Noi dung file JSON khong hop le.', 'error');
          });
      };

      const setupJsonImport = () => {
        JSON_SECTION_TYPES.forEach((type) => {
          const zone = document.querySelector('[data-json-section="' + type + '"]');
          const input = document.querySelector('[data-json-file-input="' + type + '"]');
          const pickButton = document.querySelector('[data-json-import-button="' + type + '"]');
          const clearButton = document.querySelector('[data-json-clear-button="' + type + '"]');
          if (!zone || !input) {
            return;
          }

          let dragDepth = 0;
          const highlightClasses = ['ring-2', 'ring-primary-200', 'ring-offset-2'];
          const addHighlight = () => zone.classList.add(...highlightClasses);
          const removeHighlight = () => zone.classList.remove(...highlightClasses);

          zone.addEventListener('dragenter', (event) => {
            event.preventDefault();
            dragDepth += 1;
            addHighlight();
          });

          zone.addEventListener('dragover', (event) => {
            event.preventDefault();
            if (event.dataTransfer) {
              event.dataTransfer.dropEffect = 'copy';
            }
            addHighlight();
          });

          zone.addEventListener('dragleave', (event) => {
            event.preventDefault();
            dragDepth = Math.max(0, dragDepth - 1);
            if (dragDepth === 0) {
              removeHighlight();
            }
          });

          zone.addEventListener('drop', (event) => {
            event.preventDefault();
            dragDepth = 0;
            removeHighlight();
            const files = event.dataTransfer?.files;
            if (files && files.length) {
              processSectionFile(type, files[0]);
            }
          });

          zone.addEventListener('click', (event) => {
            if (event.target instanceof HTMLElement && event.target.closest('button')) {
              return;
            }
            input.click();
          });

          zone.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              input.click();
            }
          });

          if (pickButton) {
            pickButton.addEventListener('click', () => {
              input.click();
            });
          }

          if (clearButton) {
            clearButton.addEventListener('click', () => {
              clearSectionImport(type);
            });
          }

          input.addEventListener('change', () => {
            const files = input.files;
            if (files && files.length) {
              processSectionFile(type, files[0]);
            }
            input.value = '';
          });
        });

        refreshAllImportStatuses();
      };

      setupJsonImport();
    });
  