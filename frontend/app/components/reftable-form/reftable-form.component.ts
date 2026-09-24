import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Validators } from '@librairies/@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { Observable } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { ReferenceTable } from '../../interfaces';
import { DataService } from '../../services/data.service';
import { UtilsService } from '../../services/utils.service';

@Component({
  selector: 'pnx-calc-reftable-form',
  templateUrl: './reftable-form.component.html',
  styleUrls: ['./reftable-form.component.css'],
})
export class ReferenceTableFormComponent implements OnInit {
  private static readonly MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024; // 2 Mo

  form: FormGroup;
  file: File;
  mode: 'create' | 'edit';
  referenceTable?: ReferenceTable;
  encodings: Array<string> = ['utf-8', 'latin-1'];
  separators: Array<string> = [',', ';'];
  previewHeader: Array<string>;
  previewRows: Array<Array<string>> = [];

  constructor(
    private _data: DataService,
    private _formBuilder: FormBuilder,
    private _router: Router,
    private _utils: UtilsService,
    private _route: ActivatedRoute,
    private _toastr: ToastrService
  ) {
    this.form = this._formBuilder.group({
      file: [null],
      name: ['', Validators.required],
      description: [''],
      code: ['', Validators.required],
      encoding: ['utf-8'],
      separator: [','],
    });
  }

  ngOnInit() {
    this._route.params.subscribe((params) => {
      if (params.reftableId === undefined) {
        this.mode = 'create';
        this.form.controls.file.setValidators(Validators.required);
        this.form.controls.file.updateValueAndValidity();
        return;
      }
      this.mode = 'edit';
      this.form.controls.code.disable();
      const reftableId: number = params.reftableId;
      this._data.getReferenceTables().subscribe((data: Array<ReferenceTable>) => {
        this.referenceTable = data.find((referenceTable) => referenceTable.id == reftableId);
        this.form.patchValue({
          file: null,
          name: this.referenceTable.name,
          description: this.referenceTable.description,
          code: this.referenceTable.code,
        });
      });
    });

    this.form.controls.encoding.valueChanges.subscribe(() => this._updateCSVPreview());
    this.form.controls.separator.valueChanges.subscribe(() => this._updateCSVPreview());
  }

  onFileChange(event) {
    let fileList: FileList = event.target.files;
    if (fileList.length < 1) {
      return;
    }
    const file = fileList[0];
    if (file.size > ReferenceTableFormComponent.MAX_FILE_SIZE_BYTES) {
      this._showErrorToast('Le fichier est trop volumineux. La limite est de 2 Mo.');
      event.target.value = '';
      this.file = undefined;
      this.form.controls.file.setValue(null);
      this._updateCSVPreview();
      return;
    }
    this.file = file;
    this._updateCSVPreview();
  }

  /*
   * Update the preview of the CSV content using the user-provided encoding.
   */
  private _updateCSVPreview() {
    this.previewHeader = undefined;
    this.previewRows = [];
    if (!this.file) {
      return;
    }
    const encodingMap = new Map<string, string>();
    encodingMap.set('utf-8', 'utf-8');
    encodingMap.set('latin-1', 'iso-8859-1');
    const encoding = encodingMap.get(this.form.controls.encoding.value);
    const separator = this.form.controls.separator.value;
    const numberOfLines = 3;
    const reader = new FileReader();
    reader.onload = () => {
      const lines = (reader.result as string).split(/\r\n|\r|\n/).filter((line) => line.length > 0);
      this.previewHeader = lines[0]?.split(separator);
      this.previewRows = lines.slice(1, numberOfLines + 1).map((line) => line.split(separator));
    };
    reader.readAsText(this.file, encoding);
  }

  onSubmit() {
    if (this.form.valid) {
      if (this.mode === 'create') {
        this._data
          .createReferenceTable(
            {
              name: this.form.controls.name.value,
              description: this.form.controls.description.value,
              code: this.form.controls.code.value,
              encoding: this.form.controls.encoding.value,
              separator: this.form.controls.separator.value,
            },
            this.file
          )
          .pipe(catchError((error: HttpErrorResponse) => this._handleSubmitError(error)))
          .subscribe((data: ReferenceTable) => {
            this._router.navigate(['/calculatrice/reference-tables']);
          });
      } else {
        this._data
          .editReferenceTable(
            this.referenceTable.id,
            {
              name: this.form.controls.name.value,
              description: this.form.controls.description.value,
              encoding: this.form.controls.encoding.value,
              separator: this.form.controls.separator.value,
            },
            this.file
          )
          .pipe(catchError((error: HttpErrorResponse) => this._handleSubmitError(error)))
          .subscribe((data: ReferenceTable) => {
            this._router.navigate(['/calculatrice/reference-tables']);
          });
      }
    }
  }

  private _handleSubmitError(error: HttpErrorResponse): Observable<never> {
    if (error.error) {
      Object.keys(error.error).forEach((key) => {
        const message = Array.isArray(error.error[key]) ? error.error[key][0] : error.error[key];
        this._showErrorToast(`${key}: ${message}`);
      });
    } else {
      this._showErrorToast(
        'Une erreur est survenue lors de l’enregistrement du tableau de référence.'
      );
    }
    return this._utils.handleError(error);
  }

  private _showErrorToast(message: string) {
    this._toastr.error(message, 'Erreur', {
      disableTimeOut: true,
      tapToDismiss: false,
      closeButton: true,
      easeTime: 0,
    });
  }
}
