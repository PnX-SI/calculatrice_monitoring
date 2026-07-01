import { Component, Input } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import {
  VisualizationBlockConfig,
  VisualizationBlockConfigDetails,
  VisualizationBlockConfigParam,
} from '../../../interfaces';
import { BarChartVizBlockFormComponent } from '../bar-chart-viz-block-form/bar-chart-viz-block-form.component';
import { ScalarVizBlockFormComponent } from '../scalar-viz-block-form/scalar-viz-block-form.component';

@Component({
  selector: 'pnx-calc-viz-block-form',
  templateUrl: './viz-block-form.component.html',
  styleUrls: ['./viz-block-form.component.css'],
})
export class VizBlockFormComponent {
  @Input() form: FormGroup;
  @Input() variables: string[];
  @Input() vizBlock?: VisualizationBlockConfigDetails;

  /**
   * Construit le groupe de contrôles d'un bloc de visualisation.
   * Appelé par le composant parent au moment où le bloc est ajouté au FormArray :
   * le formulaire doit être complet (validateurs compris) avant d'être affiché,
   * sinon sa validité change pendant la détection de changements.
   */
  // TODO: essayer de juste passer la liste des variables plutôt qu'une fonction
  static buildForm(
    config: VisualizationBlockConfigDetails | undefined,
    getVariables: () => string[]
  ): FormGroup {
    return new FormGroup({
      title: new FormControl(config?.title || '', { validators: Validators.required }),
      info: new FormControl(config?.info || ''),
      description: new FormControl(config?.description || ''),
      type: new FormControl(config?.type || '', {
        nonNullable: true,
        validators: Validators.required,
      }),
      params: this.buildParamsForm(config?.type, config?.params, getVariables),
    });
  }

  private static buildParamsForm(
    type: VisualizationBlockConfig['type'] | undefined,
    params: VisualizationBlockConfigParam[] | undefined,
    getVariables: () => string[]
  ): FormGroup {
    switch (type) {
      case 'bar_chart':
        return BarChartVizBlockFormComponent.buildForm(params, getVariables);
      case 'scalar':
        return ScalarVizBlockFormComponent.buildForm(params, getVariables);
      default:
        return new FormGroup({});
    }
  }

  get paramsForm() {
    return this.form.controls.params as FormGroup;
  }

  onTypeChange(event: Event) {
    const type = (event.target as HTMLSelectElement).value as VisualizationBlockConfig['type'];
    if (this.vizBlock?.params !== undefined) {
      this.vizBlock.params = [];
    }
    // Le groupe des paramètres est reconstruit ici, depuis le gestionnaire
    // d'événement, et non par le composant enfant affiché par le ngSwitch.
    this.form.setControl(
      'params',
      VizBlockFormComponent.buildParamsForm(type, this.vizBlock?.params, () => this.variables)
    );
  }
}
