import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { catchError } from 'rxjs/operators';
import { IndicatorDetails, ProtocolProperties } from '../../interfaces';
import { DataService } from '../../services/data.service';
import { UtilsService } from '../../services/utils.service';

@Component({
  selector: 'pnx-calc-indicator-code-editor',
  templateUrl: './indicator-code-editor.component.html',
  styleUrls: ['./indicator-code-editor.component.css'],
})
export class IndicatorCodeEditorComponent implements OnInit {
  indicatorForm: FormGroup;
  indicator: IndicatorDetails;
  protocolProperties: ProtocolProperties;
  scope: 'campaign' | 'overview' = 'campaign';

  constructor(
    private _data: DataService,
    private _formBuilder: FormBuilder,
    private _route: ActivatedRoute,
    private _router: Router,
    private _utils: UtilsService
  ) {
    this.indicatorForm = this._formBuilder.group({
      code: [''],
    });
  }

  ngOnInit() {
    this.scope = this._route.snapshot.data['scope'] || 'campaign';
    this._route.params.subscribe((params) => {
      this._data.getIndicatorDetails(params.indicatorId).subscribe((data: IndicatorDetails) => {
        this.indicator = data;
        const codeValue = this.scope === 'overview' ? data.overviewCode || '' : data.code;
        this.indicatorForm.controls.code.setValue(codeValue);
        this._data.getProtocolProperties(this.indicator.protocol.id).subscribe((data) => {
          this.protocolProperties = data;
        });
      });
    });
  }

  onSubmit() {
    if (this.indicatorForm.valid) {
      const save$ =
        this.scope === 'overview'
          ? this._data.editIndicatorOverviewCode(this.indicator.id, this.indicatorForm.value.code)
          : this._data.editIndicatorCode(this.indicator.id, this.indicatorForm.value.code);

      save$.pipe(catchError(this._utils.handleError)).subscribe(() => {
        this._router.navigate(['/calculatrice/indicator', this.indicator.id, 'details']);
      });
    }
  }

  insertCode(code: string) {
    const textarea = document.getElementById('code') as HTMLTextAreaElement;
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const text = this.indicatorForm.get('code')?.value || '';
      const newText = text.substring(0, start) + code + text.substring(end);
      this.indicatorForm.get('code')?.setValue(newText);
      textarea.selectionStart = textarea.selectionEnd = start + code.length;
      textarea.focus();
    }
  }
}
